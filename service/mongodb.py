from pymongo import MongoClient
import os
import logging

CONNECTION_STRING = os.getenv("MONGODB_URI", "mongodb://localhost:27017/")

_db = None

def get_db_connection():
    global _db
    if _db is not None:
        return _db

    try:
        client = MongoClient(CONNECTION_STRING)

        client.admin.command("ping")
        logging.info("Connected successfully")

        _db = client["scrob_central"]
        return _db

    except Exception as e:
        raise Exception("The following error occurred: ", e)

