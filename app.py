from flask import Flask

# Initialize the Flask application
app = Flask(__name__)

@app.route("/")
def index():
    """
    A simple route that returns a text response.
    """
    return "Hello from the single-file Python Azure Web App!"

if __name__ == "__main__":
    port = 8080
    # Run the application on the specified host and port
    app.run(host="0.0.0.0", port=port)
