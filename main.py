import os
import discord
from discord import app_commands
from dotenv import load_dotenv, find_dotenv

from henrik import get_mmr, get_mmr_history, get_account, HenrikError

load_dotenv(find_dotenv(usecwd=True))

TOKEN = os.getenv("DISCORD_TOKEN")
GUILD_ID = os.getenv("GUILD_ID")

intents = discord.Intents.default()

PRESETS: dict[str, tuple[str, str, str]] = {
    "raducu": ("eu", "RaducuXD", "4683"),
    "choppa": ("eu", "Boku wa Chopper", "0001"),
    "irinel": ("eu", "Irinel", "5555"),
    "louis": ("eu", "Boku Wa Luizao", "0001"),
    "horatiu": ("eu", "123cmboy", "EUNE"),
    "stapot": ("eu", "Mizukii", "enana"),

}

class MyClient(discord.Client):
    def __init__(self):
        super().__init__(intents=intents)
        self.tree = app_commands.CommandTree(self)

    async def setup_hook(self):
        if GUILD_ID:
            guild = discord.Object(id=int(GUILD_ID))
            self.tree.copy_global_to(guild=guild)
            await self.tree.sync(guild=guild)
        else:
            await self.tree.sync()

client = MyClient()

async def reply_or_followup(interaction: discord.Interaction, **kwargs):
    if interaction.response.is_done():
        return await interaction.followup.send(**kwargs)
    return await interaction.response.send_message(**kwargs)

@client.tree.error
async def on_app_command_error(interaction: discord.Interaction, error: app_commands.AppCommandError):
    if isinstance(error, app_commands.CommandOnCooldown):
        await reply_or_followup(
            interaction,
            content=f"Comanda e pe cooldown. Mai încearcă peste {error.retry_after:.0f}s.",
            ephemeral=True,
        )
        return
    await reply_or_followup(interaction, content=f"Eroare: `{type(error).__name__}`", ephemeral=True)
    raise error

def _mmrh_list(mmrh_payload: dict) -> list:
    data_part = mmrh_payload.get("data")
    if isinstance(data_part, dict):
        return data_part.get("history") or []
    if isinstance(data_part, list):
        return data_part
    return []

def build_embed(region: str, game_name: str, tag_line: str, mmr_payload: dict, mmrh_payload: dict, acct_payload: dict) -> discord.Embed:
    mmr = mmr_payload.get("data") or {}
    current = mmr.get("current_data") or {}

    acct = acct_payload.get("data") or {}
    name = acct.get("name") or game_name
    tag = acct.get("tag") or tag_line
    level = acct.get("account_level")

    # account card art (docs arată card URLs) [web:371]
    card = acct.get("card") or {}
    card_small = card.get("small") if isinstance(card, dict) else None

    last_update = acct.get("last_update") or acct.get("updated_at")
    last_update_raw = acct.get("last_update_raw")

    rank = current.get("currenttierpatched") or "N/A"
    rr = current.get("ranking_in_tier")
    rr_txt = f"{rr} RR" if rr is not None else "N/A"
    elo = current.get("elo")
    elo_txt = str(elo) if elo is not None else "N/A"

    # extra fields from MMR v2 (există în schema/response) [web:315]
    gndr = mmr.get("games_needed_for_rating")
    leaderboard = (mmr.get("leaderboard_placement") or {}).get("rank") if isinstance(mmr.get("leaderboard_placement"), dict) else None

    # season games via mmr-history season_id [web:314]
    history = _mmrh_list(mmrh_payload)
    current_season_id = history[0].get("season_id") if history and isinstance(history[0], dict) else None
    season_games = 0
    last_rr_change = None
    if history:
        if isinstance(history[0], dict):
            last_rr_change = history[0].get("mmr_change_to_last_game")
        if current_season_id:
            season_games = sum(1 for h in history if isinstance(h, dict) and h.get("season_id") == current_season_id)
        else:
            season_games = len(history)

    e = discord.Embed(
        title=f"VALORANT: {name}#{tag}",
        description=f"Region: {region.upper()} | Sursă: MADE BY CHOPPA,",
        color=0xE74C3C,
    )

    if card_small:
        e.set_thumbnail(url=card_small)

    e.add_field(name="Level", value=str(level) if level is not None else "N/A", inline=True)
    e.add_field(name="Rank", value="asta e prea slab sa aiba rank" if rank == "N/A" else str(rank), inline=True)
    e.add_field(name="Highest Rank", value=str(leaderboard) if leaderboard is not None else "N/A", inline=True)    e.add_field(name="RR", value=rr_txt, inline=True)
    e.add_field(name="Elo", value=elo_txt, inline=True)

    e.add_field(name="Games (current season)", value=str(season_games), inline=True)
    e.add_field(name="Last RR change", value=str(last_rr_change) if last_rr_change is not None else "N/A", inline=True)

    if gndr is not None:
        e.add_field(name="Games needed for rating", value=str(gndr), inline=True)
    if leaderboard is not None:
        e.add_field(name="Leaderboard rank", value=str(leaderboard), inline=True)

    if last_update is not None:
        e.add_field(name="Last update", value=str(last_update), inline=False)
    if last_update_raw is not None:
        e.set_footer(text=f"last_update_raw: {last_update_raw}")

    # XP până la level-up NU se poate pentru orice player doar cu name#tag fără auth (Riot tokens). [web:373]
    e.add_field(
        name="XP to next level",
        value="Necesită autentificare pe cont (nu e public pentru alți jucători).",
        inline=False,
    )

    return e

async def run_stats(interaction: discord.Interaction, region: str, game_name: str, tag_line: str):
    try:
        await interaction.response.defer(thinking=True)
    except discord.DiscordServerError:
        pass

    try:
        mmr = await get_mmr(region, game_name, tag_line)
        mmrh = await get_mmr_history(region, game_name, tag_line)
        acct = await get_account(game_name, tag_line)
        embed = build_embed(region, game_name, tag_line, mmr, mmrh, acct)
        await reply_or_followup(interaction, embed=embed)
    except HenrikError as e:
        msg = str(e)
        if len(msg) > 1800:
            msg = msg[:1800] + "..."
        await reply_or_followup(interaction, content=f"Nu am putut lua datele.\nDetalii: `{msg}`", ephemeral=True)

@client.tree.command(name="stats", description="Stats VALORANT (mai multe detalii).")
@app_commands.checks.cooldown(1, 60.0, key=lambda i: i.user.id)
@app_commands.describe(region="ex: eu, na, ap, kr", game_name="Riot gameName", tag_line="Riot tagLine")
async def stats(interaction: discord.Interaction, region: str, game_name: str, tag_line: str):
    await run_stats(interaction, region.lower(), game_name, tag_line)

@client.tree.command(name="raducu", description="Shortcut: RaducuXD#4683 (EU)")
@app_commands.checks.cooldown(1, 60.0, key=lambda i: i.user.id)
async def raducu_cmd(interaction: discord.Interaction):
    r, n, t = PRESETS["raducu"]
    await run_stats(interaction, r, n, t)

@client.tree.command(name="choppa", description="Shortcut: Boku wa Chopper#0001 (EU)")
@app_commands.checks.cooldown(1, 60.0, key=lambda i: i.user.id)
async def choppa_cmd(interaction: discord.Interaction):
    r, n, t = PRESETS["choppa"]
    await run_stats(interaction, r, n, t)

@client.tree.command(name="irinel", description="Shortcut: Irinel#5555 (EU)")
@app_commands.checks.cooldown(1, 60.0, key=lambda i: i.user.id)
async def irinel_cmd(interaction: discord.Interaction):
    r, n, t = PRESETS["irinel"]
    await run_stats(interaction, r, n, t)

@client.tree.command(name="louis", description="Shortcut: Boku wa Luizao#0001 (EU)")
@app_commands.checks.cooldown(1, 60.0, key=lambda i: i.user.id)
async def louis_cmd(interaction: discord.Interaction):
    r, n, t = PRESETS["louis"]
    await run_stats(interaction, r, n, t)

@client.tree.command(name="horatiu", description="Shortcut: 123cmboy#EUNE (EU)")
@app_commands.checks.cooldown(1, 60.0, key=lambda i: i.user.id)
async def horatiu_cmd(interaction: discord.Interaction):
    r, n, t = PRESETS["horatiu"]
    await run_stats(interaction, r, n, t)

@client.tree.command(name="stapot", description="Shortcut: Mizukii#enana (EU)")
@app_commands.checks.cooldown(1, 60.0, key=lambda i: i.user.id)
async def stapot_cmd(interaction: discord.Interaction):
    preset = PRESETS.get("stapot")
    if not preset:
        await reply_or_followup(interaction, content="Preset-ul 'stapot' nu e configurat în PRESETS.", ephemeral=True)
        return
    r, n, t = preset
    await run_stats(interaction, r, n, t)



@client.tree.command(name="help", description="Arată comenzile botului.")
async def help_cmd(interaction: discord.Interaction):
    await interaction.response.send_message(
        "**Comenzi:**\n"
        "- /stats <region> <game_name> <tag_line>\n"
        "- /raducu\n"
        "- /choppa\n"
        "- /irinel\n"
        "- /louis\n"
        "- /horatiu\n"
        "- /stapot\n\n"
        "Notă: XP până la level-up necesită autentificare pe cont (nu e public).",
        ephemeral=True,
    )

@client.event
async def on_ready():
    print(f"Logged in as {client.user} (id={client.user.id})")

if not TOKEN:
    raise RuntimeError("DISCORD_TOKEN lipsă în .env")

from web import start_web
start_web()

client.run(TOKEN)
