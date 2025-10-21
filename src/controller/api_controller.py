"""API controller for the Torob image tagging service.

This module defines the FastAPI application and all API endpoints for image analysis
and tag generation. It handles HTTP requests, validation, CORS configuration,
and integrates with the LangGraph service for image processing.
"""

from typing import Dict, Any
from fastapi import FastAPI, HTTPException, status, UploadFile, File, Request
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from dotenv import load_dotenv
from src.service.langgraph.langgraph_service import run_langgraph_on_url, run_langgraph_on_bytes
from src.config.settings import APP_NAME, APP_VERSION, DEBUG_MODE


# Load environment variables
load_dotenv()

# Initialize FastAPI application
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="AI-powered image analysis and tagging service",
    debug=DEBUG_MODE
)

# Configure CORS
allowed_origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001",
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Prometheus monitoring
Instrumentator().instrument(app).expose(app)


@app.post("/generate-tags", tags=["Image Analysis"])
async def generate_tags(request: Request, file: UploadFile = File(None)) -> Dict[str, Any]:
    """
    Unified endpoint for generating product tags from either an image URL or an uploaded file.

    This endpoint supports two input formats:
    1. JSON body with {"image_url": "<image link>"}
    2. Multipart form-data with an uploaded image file.

    The service automatically detects the input type, processes the image using the
    LangGraph module, and returns relevant tags in Persian.

    Args:
        request (Request): Incoming HTTP request that may contain JSON data.
        file (UploadFile, optional): Image file uploaded via form-data. Defaults to None.

    Returns:
        Dict[str, Any]: Generated tags and attributes in Persian.

    Raises:
        HTTPException: For invalid inputs, missing parameters, or internal processing errors.
    """
    try:
        # Case 1: File upload
        if file:
            contents = await file.read()
            result = run_langgraph_on_bytes(contents)

        # Case 2: Image URL in JSON body
        else:
            try:
                payload = await request.json()
            except Exception:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid or missing JSON body"
                )

            image_url = payload.get("image_url")
            if not image_url:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="image_url is required when no file is provided"
                )

            from urllib.parse import urlparse
            parsed = urlparse(image_url)
            if parsed.scheme not in ("http", "https"):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="URL must start with http or https"
                )

            result = run_langgraph_on_url(image_url)

        # Validate response from LangGraph
        if not isinstance(result, dict):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid response format from LangGraph service"
            )

        persian_result = result.get("persian", {})
        if not persian_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No tags generated for the provided image"
            )

        return persian_result

    except HTTPException:
        raise
    except Exception as e:
        if DEBUG_MODE:
            import traceback
            print("Unexpected error:", e)
            print(traceback.format_exc())
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Unexpected error: {e}"
        )

