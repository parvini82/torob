# Start from a Python base image
FROM python:3.10-slim

# Install Node.js and npm
RUN apt-get update && apt-get install -y \
    curl \
    && curl -fsSL https://deb.nodesource.com/setup_20.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code
COPY src ./src
COPY pyproject.toml mypy.ini ./

# Install frontend dependencies and build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Go back to app root
WORKDIR /app

# Expose ports
EXPOSE 8000 8080

# Create a startup script to run both services
RUN echo '#!/bin/bash\n\
uvicorn src.controller.api_controller:app --host 0.0.0.0 --port 8000 &\n\
cd /app/frontend && npm run build && npm start &\n\
wait -n\n\
exit $?' > /app/start.sh && chmod +x /app/start.sh

# Run both services
CMD ["/app/start.sh"]
