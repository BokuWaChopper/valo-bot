import os
import time
import aiohttp
from urllib.parse import quote
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv(usecwd=True))

BASE = "https://api.henrikdev.xyz/valorant"
CACHE_TTL = 300  # 5 min

_cache: dict[str, tuple[float, dict]] = {}

class HenrikError(Exception):
    pass

def _now() -> float:
    return time.time()

def _enc(s: str) -> str:
    return quote(str(s), safe="")

def _with_key(url: str) -> str:
    api_key = os.getenv("HENRIK_API_KEY")
    if not api_key:
        raise HenrikError("HENRIK_API_KEY lipsă în .env")
    join = "&" if "?" in url else "?"
    return f"{url}{join}api_key={_enc(api_key)}"

async def _get_json(url: str) -> dict:
    timeout = aiohttp.ClientTimeout(total=15)
    async with aiohttp.ClientSession(timeout=timeout) as session:
        async with session.get(url, headers={"Accept": "application/json"}) as r:
            raw = await r.text()
            try:
                data = await r.json(content_type=None)
            except Exception:
                raise HenrikError(f"Henrik status={r.status}, non-JSON body(first 300)={raw[:300]}")
            if r.status != 200:
                raise HenrikError(f"Henrik status={r.status}, body={data}")
            return data

async def get_mmr(region: str, name: str, tag: str) -> dict:
    key = f"mmr:{region}:{name}#{tag}".lower()
    cached = _cache.get(key)
    if cached and (_now() - cached[0] < CACHE_TTL):
        return cached[1]

    url = _with_key(f"{BASE}/v2/mmr/{_enc(region)}/{_enc(name)}/{_enc(tag)}")
    data = await _get_json(url)
    _cache[key] = (_now(), data)
    return data

async def get_mmr_history(region: str, name: str, tag: str) -> dict:
    key = f"mmrh:{region}:{name}#{tag}".lower()
    cached = _cache.get(key)
    if cached and (_now() - cached[0] < CACHE_TTL):
        return cached[1]

    url = _with_key(f"{BASE}/v1/mmr-history/{_enc(region)}/{_enc(name)}/{_enc(tag)}")
    data = await _get_json(url)
    _cache[key] = (_now(), data)
    return data

async def get_account(name: str, tag: str) -> dict:
    key = f"acct:{name}#{tag}".lower()
    cached = _cache.get(key)
    if cached and (_now() - cached[0] < CACHE_TTL):
        return cached[1]

    url = _with_key(f"{BASE}/v1/account/{_enc(name)}/{_enc(tag)}")
    data = await _get_json(url)
    _cache[key] = (_now(), data)
    return data
