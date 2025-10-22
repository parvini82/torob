import os
from redis import Redis
from rq import Worker, Queue
from dotenv import load_dotenv
from .config import Config  # Import centralized config

# Load environment variables
load_dotenv()

class RedisWorker:
    """Class to manage the Redis worker processing tasks from the queue."""
    def __init__(self):
        self.redis_host = Config.REDIS_HOST
        self.redis_port = Config.REDIS_PORT
        self.redis_connection = Redis(host=self.redis_host, port=self.redis_port)
        self.q = Queue(connection=self.redis_connection)

    def process_queue(self):
        """Start the worker to process the queue."""
        worker = Worker([self.q], connection=self.redis_connection)
        worker.work()

if __name__ == "__main__":
    # Create worker instance and start processing the queue
    worker = RedisWorker()
    worker.process_queue()
