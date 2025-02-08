# app.py
import os
from factory import create_app
from config import Config

app = create_app()

if __name__ == "__main__":
    # Use the port Azure sets, or default to 8000 locally
    port = int(os.environ.get("PORT", 8000))
    app.run(host="0.0.0.0", port=port)
