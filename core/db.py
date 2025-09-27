from pymongo import MongoClient
import os
from typing import Optional

_client: Optional[MongoClient] = None

def get_mongo_client(uri: str | None = None) -> MongoClient:
    global _client
    if _client is None:
        uri = uri or os.getenv("MONGO_URI", "mongodb://localhost:27017")
        _client = MongoClient(uri)
    return _client

def get_db(name: str | None = None):
    client = get_mongo_client()
    db_name = name or os.getenv("MONGO_DB", "lagibosan")
    return client[db_name]
