# app.py

from flask import Flask
import os

app = Flask(__name__)

@app.route("/")
def hello():
    return "Hello from Python Azure Web App! VERSION 23"

if __name__ == "__main__":
    # Azure typically sets PORT via an environment variable; default to 8000 locally
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)

