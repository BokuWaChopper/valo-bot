from flask import Flask

app = Flask(__name__)

def start_web():
    app.run(host='0.0.0.0', port=8080)

if __name__ == '__main__':
    start_web()
