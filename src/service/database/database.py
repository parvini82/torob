from datetime import datetime, timezone
from typing import Optional
from src.service.database.db_service import insert_document
from src.service.queue.redis_queue import add_to_queue


def save_request_response(image_url: str, response_data: dict) -> Optional[str]:
    document = {
        "image_url": image_url,
        "response": response_data,
        "timestamp": datetime.now(timezone.utc)  # Save the timestamp of the request
    }
    add_to_queue(process_and_save_to_db, document)
    try:
        document_id = insert_document("requests", document)
        print(f"Document inserted with ID: {document_id}")
        return document_id
    except Exception as e:
        # Log error or handle accordingly
        print(f"Failed to save request/response: {e}")
        return None

def process_and_save_to_db(document: dict) -> None:
    """Process the request and save to the database."""
    try:
        # Insert the document into the 'requests' collection in MongoDB
        insert_document("requests", document)
        print(f"Document inserted with ID: {document['_id']}")
    except Exception as e:
        print(f"Failed to save request/response to database: {e}")