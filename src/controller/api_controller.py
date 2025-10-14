from fastapi import FastAPI, UploadFile, File
from src.service.model_service import predict_tags

app = FastAPI(title="Image Tagging API")

@app.post("/predict/")
async def predict(image: UploadFile = File(...)):
    tags = predict_tags(image)
    return {"tags": tags}
