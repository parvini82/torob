from dotenv import load_dotenv
from fastapi import Body, FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator

from src.service.database.database import save_request_response
from src.service.langgraph.langgraph_service import run_langgraph_on_url, run_langgraph_on_bytes
from src.service.minio.minio_service import get_minio_service

# Load environment variables from .env at project root if present
load_dotenv()

app = FastAPI(title="Image Tagging API")

# Add Prometheus middleware and expose the /metrics endpoint
Instrumentator().instrument(app).expose(app)

# Enable CORS
origins = ["http://localhost:3000", "http://127.0.0.1:3000"]

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
async def generate_tags(payload: dict = Body(...), background_tasks: BackgroundTasks = None):
    """
    Generate tags from an image URL

    Request body:
        {
            "image_url": "http://example.com/image.jpg"
        }
    """
    image_url = payload.get("image_url")
    if not image_url:
        return {"error": "image_url is required"}

    try:
        # Call the LangGraph service to process the URL and get the response
        result = run_langgraph_on_url(image_url)

        # Queue database save as background task (non-blocking)
        if background_tasks:
            background_tasks.add_task(save_request_response, image_url, result)

        # Return only Persian JSON immediately without waiting for DB save
        return result.get("persian", {})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


@app.post("/upload-and-tag")
async def upload_and_tag(file: UploadFile = File(...), background_tasks: BackgroundTasks = None):
    """
    Upload an image file, save to MinIO, and generate tags

    Args:
        file: The uploaded image file

    Returns:
        Persian tags and the MinIO URL
    """
    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(
                status_code=400,
                detail="Only image files are allowed"
            )

        # Read file content
        file_content = await file.read()

        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")

        # Upload to MinIO first (for storage/record keeping)
        minio_service = get_minio_service()
        image_url = minio_service.upload_file(
            file_data=file_content,
            filename=file.filename,
            content_type=file.content_type
        )

        # Process with LangGraph using BYTES (not URL)
        # This converts to base64 data URI which OpenRouter can access
        result = run_langgraph_on_bytes(file_content)

        # Queue database save as background task (non-blocking)
        # This keeps the API response fast
        if background_tasks:
            background_tasks.add_task(save_request_response, image_url, result)

        # Return Persian tags along with the MinIO URL immediately
        return {
            "image_url": image_url,
            "tags": result.get("persian", {}),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing upload: {str(e)}")
