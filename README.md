# torob
version: '3.9'

services:
  db:
    image: postgres:15
    container_name: torob_db
    restart: always
    environment:
      POSTGRES_USER: torob_user
      POSTGRES_PASSWORD: torob_pass
      POSTGRES_DB: torob_db
    volumes:
      - db_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"

  api:
    build: .
    container_name: torob_api
    restart: always
    depends_on:
      - db
    environment:
      DATABASE_URL: postgresql+psycopg2://torob_user:torob_pass@db:5432/torob_db
    ports:
      - "8000:8000"
    volumes:
      - .:/app
    command: uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

volumes:
  db_data:
