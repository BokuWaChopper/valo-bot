import discord

def _find_first_stat(segments: list, keys: list[str]):
    for seg in segments or []:
        stats = (seg.get("stats") or {})
        for k in keys:
            if k in stats:
                return stats[k]
    return None

def _stat_value(stat_obj):
    if not stat_obj:
        return None
    return stat_obj.get("displayValue") or stat_obj.get("value")

def build_stats_embed(payload: dict, game_name: str, tag_line: str) -> discord.Embed:
    data = payload.get("data") or {}
    platform_info = data.get("platformInfo") or {}
    user_handle = platform_info.get("platformUserHandle") or f"{game_name}#{tag_line}"
    avatar = platform_info.get("avatarUrl")

    segments = data.get("segments") or []

    level = _stat_value(_find_first_stat(segments, ["level"]))
    rank = _stat_value(_find_first_stat(segments, ["rank", "competitiveTier"]))
    matches = _stat_value(_find_first_stat(segments, ["matchesPlayed", "matches"]))
    wins = _stat_value(_find_first_stat(segments, ["wins"]))
    kd = _stat_value(_find_first_stat(segments, ["kd", "kDRatio"]))

    e = discord.Embed(
        title=f"VALORANT Stats: {user_handle}",
        description="Powered By Tracker Network",
        color=0xE74C3C,
    )

    if avatar:
        e.set_thumbnail(url=avatar)

    e.add_field(name="Level", value=str(level or "N/A"), inline=True)
    e.add_field(name="Rank", value=str(rank or "N/A"), inline=True)
    e.add_field(name="Matches", value=str(matches or "N/A"), inline=True)
    e.add_field(name="Wins", value=str(wins or "N/A"), inline=True)
    e.add_field(name="K/D", value=str(kd or "N/A"), inline=True)
    return e
