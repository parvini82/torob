import os

from dotenv import load_dotenv

load_dotenv()

MINIO_CONFIG = {
    "url": os.getenv("MINIO_URL", "http://minio:9000"),
    "access_key": os.getenv("MINIO_ACCESS_KEY"),
    "secret_key": os.getenv("MINIO_SECRET_KEY"),
    "bucket_name": os.getenv("MINIO_BUCKET_NAME", "image-tagging"),
}
