# FROM python:3.10-slim
# WORKDIR /app
# COPY requirements.txt .
# RUN pip install --no-cache-dir -r requirements.txt
# COPY . .
# EXPOSE 8000
# CMD ["uvicorn", "src.controller.api_controller:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "src"]

FROM node:20-alpine
WORKDIR /app
COPY frontend/package.json .
RUN npm install
COPY frontend/ .
EXPOSE 3000
CMD ["sh", "-c", "npm ci && npm run build && npm run start"]
