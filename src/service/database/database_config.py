import os

# Database Configuration
DB_HOST = os.getenv("DB_HOST", default="localhost")
DB_PORT = int(os.getenv("DB_PORT", default="27017"))
DB_NAME = os.getenv("DB_NAME", default="project_database")
DB_USER = os.getenv("DB_USER", default=None)  # Optional for MongoDB (or other DBs with auth)
DB_PASSWORD = os.getenv("DB_PASSWORD", default=None)  # Optional for MongoDB (or other DBs with auth)
