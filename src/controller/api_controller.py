from fastapi import FastAPI, UploadFile, File, Body
from fastapi.middleware.cors import CORSMiddleware
from src.service.langgraph.langgraph_service import run_langgraph_on_bytes, run_langgraph_on_url
from dotenv import load_dotenv

# Load environment variables from .env at project root if present
load_dotenv()

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

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/generate-tags")
async def generate_tags(payload: dict = Body(...)):
    image_url = payload.get("image_url")
    if not image_url:
        return {"error": "image_url is required"}
    result = run_langgraph_on_url(image_url)
    # Return only Persian JSON as requested
    return result.get("persian", {})
