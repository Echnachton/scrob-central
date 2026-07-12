from pymongo import MongoClient

CONNECTION_STRING = "mongodb://localhost:27017/"

_db = None

def get_db_connection():
    global _db
    if _db is not None:
        return _db

    try:
        client = MongoClient(CONNECTION_STRING)

        client.admin.command("ping")
        print("Connected successfully")

        _db = client["scrob_central"]
        return _db

    except Exception as e:
        raise Exception("The following error occurred: ", e)

