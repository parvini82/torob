import os

from dotenv import load_dotenv

load_dotenv()
DB_HOST = os.getenv("DB_HOST", "")
DB_PORT = int(os.getenv("DB_PORT", ""))
DB_NAME = os.getenv("DB_NAME", "torob")
DB_USER = os.getenv("DB_USER", None)  # Optional for MongoDB (or other DBs with auth)
DB_PASSWORD = os.getenv(
    "DB_PASSWORD", None
)  # Optional for MongoDB (or other DBs with auth)
