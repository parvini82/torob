from datetime import datetime, timezone
from typing import Optional
from src.service.database.db_service import insert_document


def save_request_response(image_url: str, response_data: dict) -> Optional[str]:
    document = {
        "image_url": image_url,
        "response": response_data,
        "timestamp": datetime.now(timezone.utc)  # Save the timestamp of the request
    }

    try:
        document_id = insert_document("requests", document)
        print(f"Document inserted with ID: {document_id}")
        return document_id
    except Exception as e:
        # Log error or handle accordingly
        print(f"Failed to save request/response: {e}")
        return None