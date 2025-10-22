from pymongo import MongoClient

# MongoDB Client Setup
client = MongoClient("mongodb://localhost:27017/")
db = client["torob"]
collection = db["requests"]


# Define the document structure
def save_request_response():

    document = {
        "image_url": "image_url",
        "response": "response_data",
        "timestamp": "datetime.now(timezone.utc)",  # Save the timestamp of the request
    }

    result = None  # Initialize the result variable outside the try block

    try:
        result = collection.insert_one(document)
        print(f"Document inserted with ID: {result.inserted_id}")
    except Exception as e:
        # Log error or handle accordingly (does not affect user response)
        print(f"Failed to save request/response: {e}")

    if result:
        return str(
            result.inserted_id
        )  # Return the document ID if insertion was successful
    return None  # Return None if there was an error


if __name__ == "__main__":
    save_request_response()
