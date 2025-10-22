from dotenv import load_dotenv
from redis import Redis
from rq import Queue

from .config import Config  # Import centralized config

# Load environment variables
load_dotenv()


class RedisQueue:
    """Class to manage Redis connection and task queue."""

    def __init__(self):
        self.redis_host = Config.REDIS_HOST
        self.redis_port = Config.REDIS_PORT
        self.redis_connection = Redis(host=self.redis_host, port=self.redis_port)
        self.q = Queue(connection=self.redis_connection)

    def add_to_queue(self, func, *args, **kwargs):
        """Add a task to the Redis queue."""
        self.q.enqueue(func, *args, **kwargs)
