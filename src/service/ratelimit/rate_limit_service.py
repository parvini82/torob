import time
from redis import Redis
from datetime import timedelta

class RateLimitService:
    def __init__(self, redis_client: Redis, limit: int = 10, window_seconds: int = 60):
        self.redis = redis_client
        self.limit = limit
        self.window_seconds = window_seconds

    def is_rate_limited(self, ip: str) -> bool:
        # Get the current count of requests for this IP
        current_count = self.redis.get(ip)
        if current_count is None:
            self.redis.set(ip, 1, ex=self.window_seconds)
            return False
        elif int(current_count) < self.limit:
            self.redis.incr(ip)
            return False
        return True
