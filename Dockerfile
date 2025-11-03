FROM python:3.10-slim as backend
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY src ./src
CMD ["uvicorn", "src.controller.api_controller:app", "--host", "0.0.0.0", "--port", "8000"]

FROM node:20-alpine as frontend
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build
CMD ["npm", "run", "start"]

FROM nginx:alpine
COPY --from=frontend /app/frontend/.next /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE $PORT
