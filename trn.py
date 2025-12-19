import os
import time
import aiohttp
from urllib.parse import quote
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(usecwd=True))

BASE = "https://api.tracker.gg/api/v2/valorant/standard"

CACHE_TTL = 300  # 5 minute
_cache: dict[str, tuple[float, dict]] = {}

class TrnError(Exception):
    pass

def riot_id_url(game_name: str, tag_line: str) -> str:
    return quote(f"{game_name}#{tag_line}", safe="")

def _now() -> float:
    return time.time()

async def trn_get_profile(game_name: str, tag_line: str, *, force_collect: bool = False) -> dict:
    trn_api_key = os.getenv("TRN_API_KEY")
    if not trn_api_key:
        raise TrnError("TRN_API_KEY lipsă în .env")

    riot = riot_id_url(game_name, tag_line)
    cache_key = f"profile:{riot}"

    cached = _cache.get(cache_key)
    if cached and (_now() - cached[0] < CACHE_TTL):
        return cached[1]

    url = f"{BASE}/profile/riot/{riot}"
    if force_collect:
        url += "?forceCollect=true"

    headers = {
        "TRN-Api-Key": trn_api_key,  # TRN auth header [web:29]
        "User-Agent": "DiscordBot (valorant-stats)",
        "Accept": "application/json,text/plain,*/*",
    }

    timeout = aiohttp.ClientTimeout(total=15)

    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, headers=headers) as r:
            raw = await r.text()

            # Nu mai crăpăm pe non-JSON (ex: HTML block page)
            try:
                data = await r.json(content_type=None)
            except Exception:
                raise TrnError(f"TRN status={r.status}, non-JSON body(first 300)={raw[:300]}")

            if r.status != 200:
                raise TrnError(f"TRN status={r.status}, body={data}")

            _cache[cache_key] = (_now(), data)
            return data
