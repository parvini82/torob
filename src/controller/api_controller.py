import os
from fastapi import FastAPI, Body, File, UploadFile, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import APIKeyHeader
from dotenv import load_dotenv

from src.service.langgraph.langgraph_service import run_langgraph_on_url, run_langgraph_on_bytes

# ---------------------------------------------------------------------------
# Environment and Application Setup
# ---------------------------------------------------------------------------

load_dotenv()

app = FastAPI(title="Image Tagging API")

# CORS configuration
origins = ["http://localhost:3000", "http://127.0.0.1:3000","https://torob-production.up.railway.app"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Authentication and Token Configuration
# ---------------------------------------------------------------------------

API_TOKENS = os.getenv("API_TOKENS", "").split(",")
if not API_TOKENS or API_TOKENS == [""]:
    raise ValueError("Environment variable API_TOKENS must be set with one or more comma-separated tokens.")

api_key_header = APIKeyHeader(name="Authorization", auto_error=True)

# ---------------------------------------------------------------------------
# Utility Functions
# ---------------------------------------------------------------------------

def verify_internal_access(request: Request) -> None:
    """
    Restrict access to internal endpoints.
    Allows requests only from localhost (127.0.0.1 or ::1).
    Raises:
        HTTPException: if the request originates from an external IP.
    """
    client_ip = request.client.host
    if client_ip not in ("127.0.0.1", "::1"):
        raise HTTPException(status_code=403, detail="Access denied: internal use only.")

# ---------------------------------------------------------------------------
# Health Check Endpoint
# ---------------------------------------------------------------------------

@app.get("/health")
async def health() -> dict:
    """Simple health check endpoint."""
    return {"status": "ok"}

# ---------------------------------------------------------------------------
# Internal Endpoints (Restricted to Localhost)
# ---------------------------------------------------------------------------

@app.post("/generate-tags")
async def generate_tags(payload: dict = Body(...), request: Request = None) -> dict:
    """
    Internal endpoint: Generate tags from an image URL.
    Accessible only from within the server.
    """
    verify_internal_access(request)

    image_url = payload.get("image_url")
    if not image_url:
        raise HTTPException(status_code=400, detail="Field 'image_url' is required.")

    try:
        result = run_langgraph_on_url(image_url)
        return result.get("persian", {})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image processing failed: {e}")

@app.post("/upload-and-tag")
async def upload_and_tag(file: UploadFile = File(...), request: Request = None) -> dict:
    """
    Internal endpoint: Upload an image file and generate tags.
    Accessible only from within the server.
    """
    verify_internal_access(request)

    try:
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Invalid file type. Only images are allowed.")

        file_content = await file.read()
        if not file_content:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")

        result = run_langgraph_on_bytes(file_content)
        return {"tags": result.get("persian", {})}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload processing failed: {e}")

# ---------------------------------------------------------------------------
# External Endpoint (Public Access with Token Authentication)
# ---------------------------------------------------------------------------

@app.post("/external-generate-tags")
async def external_generate_tags(
    payload: dict = Body(...),
    api_token: str = Depends(api_key_header),
) -> dict:
    """
    Public endpoint: Generate tags for an image using a secure API token.

    Request Body:
        {
            "image_url": "https://example.com/image.jpg",
            "mode": "fast"
        }

    Authorization:
        Header: Authorization: <api_token>
    """
    if api_token not in API_TOKENS:
        raise HTTPException(status_code=403, detail="Invalid or missing API token.")

    image_url = payload.get("image_url")
    if not image_url:
        raise HTTPException(status_code=400, detail="Field 'image_url' is required.")

    mode = payload.get("mode", "fast")

    try:
        result = run_langgraph_on_url(image_url,mode=mode)
        return {"mode": mode, "tags": result.get("persian", {})}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"External image processing failed: {e}")
