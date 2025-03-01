import gridfs
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


    def find_and_delete(self, collection:str, query):
        collection = self.db[collection]

        docs = list(collection.find(query))

        for doc in docs:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])

        collection.delete_many(query)

        return docs

    def update_field(self, collection: str, query: dict, field: str, value: any) -> int:
        """
        Updates the specified field to value for all documents matching the query.

        Args:
            collection: Name of the MongoDB collection
            query: MongoDB filter query
            field: Field to update
            value: New value for the field

        Returns:
            Number of documents modified
        """
        collection_obj = self.db[collection]
        update_result = collection_obj.update_many(query, {"$set": {field: value}})
        return update_result.modified_count

    def increment_field(self, collection: str, query: dict, field: str, amount: int) -> int:
        """
        Increments the specified field by the given amount for matching documents.

        Args:
            collection: Name of the MongoDB collection
            query: MongoDB filter query
            field: Field to increment
            amount: Amount to increment by

        Returns:
            Number of documents modified
        """
        collection_obj = self.db[collection]
        update_result = collection_obj.update_many(query, {"$inc": {field: amount}})
        return update_result.modified_count


    def collection_size(self, collection: str):
        return self.db[collection].count_documents({})

    def create_collection(self, collection: str):
        self.db.create_collection(collection)

    def add(self, collection: str, file: dict):
        """
        Pass in an arbitrary collection and file, will add it
        """
        collection = self.db[collection]
        return collection.insert_one(file)

    def query_one_attribute(self, collection: str, attribute: str, value) -> list:
        query_filter = {attribute: value}
        cursor = self.db[collection].find(query_filter)

        #convert the cursor to a list
        results = list(cursor)

        # Convert each document's '_id' from ObjectId to string for compatibility
        for doc in results:
            if "_id" in doc:
                doc["_id"] = str(doc["_id"])

        return results

    def get_one(self,collection: str, query: dict) -> dict:
        collection = self.db[collection]
        return collection.find_one(query)

    def get_all(self, collection: str):
        collection = self.db[collection]
        return list(collection.find({}))

    def num_items_query(self, collection: str, query):
        collection = self.db[collection]
        return collection.count_documents(query)


    #METHODS for GRID FS:

    def get_file_gridfs(self, task_id: str):
        fs = gridfs.GridFS(self.db)
        doc = self.db.fs.files.find_one({"metadata.task_id": task_id})
        if doc and "_id" in doc:
            return fs.get(doc["_id"])
        else:
            return None










