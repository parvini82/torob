from fastapi import FastAPI, UploadFile
from src.service.model_service import predict_tags

app = FastAPI(title="Image Tagging API")

@app.post("/predict/")
async def predict(image: UploadFile):
    result = predict_tags(image)
    return {"tags": result}
