import os
import certifi
from flask import Flask
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

###############################################################################
# Single-file Flask application with MongoDB integration
###############################################################################

app = Flask(__name__)

# Hard-coded MongoDB connection URI
# Replace this with your actual MongoDB connection string if you want to change it.
# This is NOT reading from environment variables.
MONGODB_URI = "mongodb+srv://ahurlbut999:MluzrXgAfj1Jf4yF@server-tasks.kszyt.mongodb.net/?retryWrites=true&w=majority"

# Instantiate the database client using the URI
client = MongoClient(
    MONGODB_URI,
    server_api=ServerApi('1'),
    tlsCAFile=certifi.where()  # Ensure we validate SSL certificates properly
)

# Verify that we can connect to MongoDB right away
try:
    client.admin.command("ping")
    print("Successfully connected to MongoDB!")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    raise e

@app.route("/")
def index():
    """
    A simple route that returns a text response.
    """
    return "Hello from the single-file Python Azure Web App!"

@app.route("/test-db")
def test_db():
    """
    A route to test inserting a small document into MongoDB.
    Useful for confirming connectivity and verifying
    that DB operations succeed in Azure.
    """
    try:
        # Access or create a test collection
        db = client["test_db"]
        collection = db["test_collection"]
        # Insert a sample document
        result = collection.insert_one({"message": "Hello from Azure (single-file)!"})
        return f"Successfully inserted document with _id: {result.inserted_id}"
    except Exception as e:
        return f"Error while interacting with MongoDB: {e}"

if __name__ == "__main__":
    # By default, let's just run on port 8000
    # (Azure often sets PORT externally, but this is a fallback approach)
    port = 8000
    # Binding to 0.0.0.0 so that the app is reachable from any external interface
    app.run(host="0.0.0.0", port=port)
