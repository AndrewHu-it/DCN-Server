# database.py
import certifi
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

class Database:
    def __init__(self, uri: str):
        """
        Initialize the database connection using the provided URI.
        We also ping the server to ensure connectivity.
        """
        self.client = MongoClient(
            uri,
            server_api=ServerApi('1'),
            tlsCAFile=certifi.where()  # Ensures SSL certificates are properly verified
        )

        # Verify connection on startup by pinging the admin DB
        try:
            self.client.admin.command("ping")
            print("Successfully connected to MongoDB!")
        except Exception as e:
            print(f"Error connecting to MongoDB: {e}")
            raise e

    def get_collection(self, db_name: str, collection_name: str):
        """
        A helper method to retrieve a collection handle easily.
        """
        db = self.client[db_name]
        return db[collection_name]
