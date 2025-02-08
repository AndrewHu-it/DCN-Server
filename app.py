
from flask import Flask

@app.route("/")
def index():
    """
    A simple route that returns a text response.
    """
    return "Hello from the single-file Python Azure Web App!"


if __name__ == "__main__":
    port = 8000
    app.run(host="0.0.0.0", port=port)
