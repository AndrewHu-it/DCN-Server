# factory.py
from flask import Flask
from config import Config
from database import Database

def create_app():
    """
    The application factory.
    This function creates and configures the Flask application, sets up database, etc.
    """
    app = Flask(__name__)

    # Initialize the database
    db = Database(Config.MONGODB_URI)

    # Example route: simple home page
    @app.route("/")
    def index():
        return "Hello from Python Azure Web App! This is a test."

    # Optional route to demonstrate a DB operation
    @app.route("/test-db")
    def test_db():
        try:
            collection = db.get_collection("test_db", "test_collection")
            result = collection.insert_one({"message": "Hello from Azure (via factory)!"})
            return f"Successfully inserted document with _id: {result.inserted_id}"
        except Exception as e:
            return f"Error while interacting with MongoDB: {e}"

    return app
