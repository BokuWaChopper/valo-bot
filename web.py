from flask import Flask
import threading

app = Flask(__name__)

@app.route('/')
def home():
    return 'Bot is running!', 200

def start_web():
    # Run Flask in a separate thread so it doesn't block the bot
    thread = threading.Thread(target=lambda: app.run(host='0.0.0.0', port=8080, debug=False))
    thread.daemon = True
    thread.start()

@app.route('/valorant/<region>/<game_name>/<tag_line>')
async def get_valorant_stats(region, game_name, tag_line):
    try:
        from henrik import get_mmr, get_mmr_history, get_account
        from main import build_embed
        
        mmr = await get_mmr(region, game_name, tag_line)
        mmrh = await get_mmr_history(region, game_name, tag_line)
        acct = await get_account(game_name, tag_line)
        
        embed = build_embed(region, game_name, tag_line, mmr, mmrh, acct)
        
        # Convert embed to dictionary for JSON response
        embed_data = {
            "title": embed.title,
            "description": embed.description,
            "color": embed.color,
            "fields": []
        }
        
        for field in embed.fields:
            embed_data["fields"].append({
                "name": field.name,
                "value": field.value,
                "inline": field.inline
            })
        
        if embed.thumbnail:
            embed_data["thumbnail"] = embed.thumbnail.url
        
        return embed_data, 200
    except Exception as e:
        return {"error": str(e)}, 400

