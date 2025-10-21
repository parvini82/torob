from pymongo import MongoClient
from .database_config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD
from typing import Optional, Dict, Any

def get_db_client() -> MongoClient:
    """Create and return a MongoDB client."""
    if DB_USER and DB_PASSWORD:
        db_uri = f"mongodb://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/"
    else:
        db_uri = f"mongodb://{DB_HOST}:{DB_PORT}/"
    client = MongoClient(db_uri)
    return client

def get_database() -> MongoClient:
    """Get the MongoDB database instance."""
    client = get_db_client()
    return client[DB_NAME]

def insert_document(collection_name: str, document: Dict[str, Any]) -> str:
    """Insert a new document into a collection."""
    db = get_database()
    collection = db[collection_name]
    result = collection.insert_one(document)
    return str(result.inserted_id)

def find_document(collection_name: str, query: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Find a document by query in the specified collection."""
    db = get_database()
    collection = db[collection_name]
    document = collection.find_one(query)
    return document

def update_document(collection_name: str, query: Dict[str, Any], update_values: Dict[str, Any]) -> bool:
    """Update a document in the collection."""
    db = get_database()
    collection = db[collection_name]
    result = collection.update_one(query, {"$set": update_values})
    return result.modified_count > 0

def delete_document(collection_name: str, query: Dict[str, Any]) -> bool:
    """Delete a document from the collection."""
    db = get_database()
    collection = db[collection_name]
    result = collection.delete_one(query)
    return result.deleted_count > 0

def count_documents(collection_name: str, query: Dict[str, Any] = {}) -> int:
    """Count the number of documents that match a query."""
    db = get_database()
    collection = db[collection_name]
    return collection.count_documents(query)
