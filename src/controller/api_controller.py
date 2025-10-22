from dotenv import load_dotenv
from fastapi import Body, FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from src.service.langgraph.langgraph_service import run_langgraph_on_url, run_langgraph_on_bytes

# Load environment variables from .env at project root if present
load_dotenv()

app = FastAPI(title="Image Tagging API")

# Add Prometheus middleware and expose the /metrics endpoint

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
async def generate_tags(payload: dict = Body(...)):
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

        # Return only Persian JSON result
        return result.get("persian", {})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


@app.post("/upload-and-tag")
async def upload_and_tag(file: UploadFile = File(...)):
    """
    Upload an image file and generate tags

    Args:
        file: The uploaded image file

    Returns:
        Persian tags
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

        # Process with LangGraph using BYTES (not URL)
        # This converts to base64 data URI which OpenRouter can access
        result = run_langgraph_on_bytes(file_content)

        # Return Persian tags immediately
        return {
            "tags": result.get("persian", {}),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing upload: {str(e)}")
