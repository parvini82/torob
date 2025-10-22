import os
import uuid
from io import BytesIO
from typing import Optional

from minio import Minio
from minio.error import S3Error


class MinIOService:
    def __init__(self):
        # Parse MINIO_URL to extract host and port
        minio_url = os.getenv("MINIO_URL", "http://minio:9000")
        # Remove http:// or https://
        minio_host = minio_url.replace("http://", "").replace("https://", "")

        self.client = Minio(
            minio_host,
            access_key=os.getenv("MINIO_ACCESS_KEY"),
            secret_key=os.getenv("MINIO_SECRET_KEY"),
            secure=False  # Set to True if using HTTPS
        )
        self.bucket_name = os.getenv("MINIO_BUCKET_NAME", "image-tagging")
        self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        try:
            if not self.client.bucket_exists(self.bucket_name):
                self.client.make_bucket(self.bucket_name)
                # Set public read policy for easy access
                policy = {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"AWS": "*"},
                            "Action": ["s3:GetObject"],
                            "Resource": [f"arn:aws:s3:::{self.bucket_name}/*"]
                        }
                    ]
                }
                import json
                self.client.set_bucket_policy(self.bucket_name, json.dumps(policy))
        except S3Error as e:
            print(f"Error creating bucket: {e}")

    def upload_file(
            self,
            file_data: bytes,
            filename: Optional[str] = None,
            content_type: str = "image/jpeg"
    ) -> str:
        """
        Upload file to MinIO and return the URL

        Args:
            file_data: The file content as bytes
            filename: Original filename (optional)
            content_type: MIME type of the file

        Returns:
            The public URL of the uploaded file
        """
        try:
            # Generate unique filename
            if filename:
                extension = filename.rsplit(".", 1)[-1] if "." in filename else "jpg"
            else:
                extension = "jpg"

            unique_filename = f"{uuid.uuid4()}.{extension}"

            # Upload to MinIO
            self.client.put_object(
                self.bucket_name,
                unique_filename,
                BytesIO(file_data),
                length=len(file_data),
                content_type=content_type
            )

            # Construct the URL
            minio_url = os.getenv("MINIO_URL", "http://localhost:9000")
            file_url = f"{minio_url}/{self.bucket_name}/{unique_filename}"

            return file_url

        except S3Error as e:
            raise Exception(f"Failed to upload to MinIO: {e}")

    def delete_file(self, filename: str) -> bool:
        """Delete a file from MinIO"""
        try:
            self.client.remove_object(self.bucket_name, filename)
            return True
        except S3Error as e:
            print(f"Error deleting file: {e}")
            return False


# Singleton instance
_minio_service = None


def get_minio_service() -> MinIOService:
    global _minio_service
    if _minio_service is None:
        _minio_service = MinIOService()
    return _minio_service
