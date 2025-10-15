FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "src.controller.api_controller:app", "--host", "0.0.0.0", "--port", "8000", "--reload", "--reload-dir", "src"]
