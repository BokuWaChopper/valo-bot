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
