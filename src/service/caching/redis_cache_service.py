"""Redis caching service for image tagging API"""

import hashlib
import json
from typing import Optional, Dict, Any
from redis.asyncio import Redis, ConnectionPool
import os


class RedisCacheService:
    """Redis caching service using SHA-256 content hashing"""

    def __init__(self):
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        self.pool = ConnectionPool.from_url(
            redis_url,
            max_connections=20,
            decode_responses=True
        )
        self.default_ttl = 60 * 60  # 1 hour

    async def get_redis_client(self) -> Redis:
        return Redis(connection_pool=self.pool)

    @staticmethod
    def generate_image_hash(image_data: bytes) -> str:
        """Generate SHA-256 hash from image bytes"""
        return hashlib.sha256(image_data).hexdigest()

    def _create_cache_key(self, hash_value: str, prefix: str = "image_tags") -> str:
        return f"{prefix}:{hash_value}"

    async def get_cached_tags(self, image_hash: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached tags for an image"""
        redis_client = await self.get_redis_client()
        try:
            cache_key = self._create_cache_key(image_hash)
            cached_data = await redis_client.get(cache_key)
            if cached_data:
                return json.loads(cached_data)
            return None
        finally:
            await redis_client.aclose()

    async def set_cached_tags(
            self,
            image_hash: str,
            tags_data: Dict[str, Any],
            ttl: Optional[int] = None
    ) -> bool:
        """Store tags in cache"""
        redis_client = await self.get_redis_client()
        try:
            cache_key = self._create_cache_key(image_hash)
            ttl_seconds = ttl or self.default_ttl
            serialized_data = json.dumps(tags_data)
            await redis_client.setex(cache_key, ttl_seconds, serialized_data)
            return True
        except Exception as e:
            print(f"Error caching tags: {e}")
            return False
        finally:
            await redis_client.aclose()

    async def clear_all_cache(self) -> int:
        """Clear all cached image tags"""
        redis_client = await self.get_redis_client()
        try:
            cursor = 0
            deleted_count = 0
            pattern = self._create_cache_key("*")
            while True:
                cursor, keys = await redis_client.scan(cursor, match=pattern, count=100)
                if keys:
                    deleted_count += await redis_client.delete(*keys)
                if cursor == 0:
                    break
            return deleted_count
        finally:
            await redis_client.aclose()

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        redis_client = await self.get_redis_client()
        try:
            info = await redis_client.info("stats")
            cursor = 0
            key_count = 0
            pattern = self._create_cache_key("*")
            while True:
                cursor, keys = await redis_client.scan(cursor, match=pattern, count=100)
                key_count += len(keys)
                if cursor == 0:
                    break
            return {
                "total_cached_images": key_count,
                "redis_memory_used": info.get("used_memory_human", "N/A"),
                "total_connections": info.get("total_connections_received", 0),
                "total_commands": info.get("total_commands_processed", 0),
            }
        finally:
            await redis_client.aclose()

    async def close(self):
        """Close the connection pool"""
        await self.pool.aclose()


# Singleton instance
_cache_service_instance: Optional[RedisCacheService] = None


def get_cache_service() -> RedisCacheService:
    """Get or create singleton cache service instance"""
    global _cache_service_instance
    if _cache_service_instance is None:
        _cache_service_instance = RedisCacheService()
    return _cache_service_instance
