from bson import ObjectId
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from pymongo.errors import ConnectionFailure



class DataBase:
    __slots__ = ['client', 'db']

    def __init__(self, connection_string, db_name):

        try:
            self.client = MongoClient(connection_string, server_api=ServerApi('1'))
            self.client.admin.command('ping')
            print("Pinged your deployment. You successfully connected to MongoDB!")
        except ConnectionFailure as e:
            print(f"Failed to connect to MongoDB: {e}")
            raise


        self.db = self.client[db_name]






    #Official Method
    def add(self, collection: str, file: dict):
        """
        Pass in an arbitrary collection and file, will add it
        """

        collection = self.db[collection]
        return collection.insert_one(file)

    def query(self, collection: str, attribute: str, value) -> list:
        query_filter = {attribute: value}
        # Perform the MongoDB find operation, which returns a cursor
        cursor = self.db[collection].find(query_filter)

        # Convert the cursor to a list
        results = list(cursor)

        # Convert each document's '_id' from ObjectId to string for compatibility
        for doc in results:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])

        return results



