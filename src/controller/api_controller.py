from fastapi import FastAPI, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from src.service.model_service import predict_tags

app = FastAPI(title="Image Tagging API")

# فعال کردن CORS
origins = [
    "http://localhost:3000",  # آدرس فرانت‌اند شما
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/predict/")
async def predict(image: UploadFile):
    result = predict_tags(image)
    return {"tags": result}
