from src.config.settings import get_minio_client

minio_client = get_minio_client()


def upload_image_to_minio(image_path, object_name):
    minio_client.fput_object("clothing-images", object_name, image_path)


def download_image_from_minio(object_name, download_path):
    minio_client.fget_object("clothing-images", object_name, download_path)
