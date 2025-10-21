from src.config.settings import get_redis_client

redis_client = get_redis_client()

def cache_image_tag(image_id, tag):
    redis_client.setex(image_id, 3600, tag)

def get_cached_tag(image_id):
    tag = redis_client.get(image_id)
    if tag:
        return tag
    return None
