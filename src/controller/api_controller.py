from fastapi import BackgroundTasks, Body, FastAPI, HTTPException, Request, File, UploadFile
from src.service.ratelimit.rate_limit_service import RateLimitService
from src.service.caching.redis_cache_service import RedisCacheService, get_cache_service
from src.service.database.database import save_request_response
from src.service.langgraph.langgraph_service import run_langgraph_on_bytes, run_langgraph_on_url
from src.service.minio.minio_service import get_minio_service
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from redis import Redis
from dotenv import load_dotenv

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

# Initialize Redis client (ensure it's correctly configured)
redis_client = Redis(host="redis", port=6379, db=0)  # Adjust as needed
rate_limit_service = RateLimitService(redis_client=redis_client, limit=10, window_seconds=60)

@app.get("/health")
async def health():
    return {"status": "ok"}

# Rate Limit check
async def check_rate_limit(request: Request):
    ip = request.client.host
    if rate_limit_service.is_rate_limited(ip):
        raise HTTPException(status_code=429, detail="Rate limit exceeded. Please try again later.")

@app.post("/generate-tags")
async def generate_tags(
    payload: dict = Body(...),
    background_tasks: BackgroundTasks = None,
    request: Request = None  # Added request dependency for IP check
):
    await check_rate_limit(request)  # Check rate limit

    image_url = payload.get("image_url")
    if not image_url:
        return {"error": "image_url is required"}

    # Generate the image hash for caching
    image_hash = RedisCacheService.generate_image_hash(image_url.encode('utf-8'))

    # Check if the tags are already cached
    cache_service = get_cache_service()
    cached_tags = await cache_service.get_cached_tags(image_hash)

    if cached_tags:
        # If tags are cached, return them directly
        return cached_tags

    try:
        # If not cached, call the LangGraph service to process the URL and get the response
        result = run_langgraph_on_url(image_url)

        # Store the generated tags in the Redis cache
        await cache_service.set_cached_tags(image_hash, result.get("persian", {}))

        # Queue database save as background task (non-blocking)
        if background_tasks:
            background_tasks.add_task(save_request_response, image_url, result)

        return result.get("persian", {})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")


@app.post("/upload-and-tag")
async def upload_and_tag(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    request: Request = None  # Added request dependency for IP check
):
    await check_rate_limit(request)  # Check rate limit

    try:
        # Validate file type
        if not file.content_type or not file.content_type.startswith("image/"):
            raise HTTPException(status_code=400, detail="Only image files are allowed")

        # Read file content
        file_content = await file.read()

        if len(file_content) == 0:
            raise HTTPException(status_code=400, detail="Empty file uploaded")

        # Generate the image hash for caching
        image_hash = RedisCacheService.generate_image_hash(file_content)

        # Check if the tags are already cached
        cache_service = get_cache_service()
        cached_tags = await cache_service.get_cached_tags(image_hash)

        if cached_tags:
            # If tags are cached, return them directly
            return {"image_url": "cached", "tags": cached_tags}

        # Upload to MinIO first (for storage/record keeping)
        minio_service = get_minio_service()
        image_url = minio_service.upload_file(
            file_data=file_content,
            filename=file.filename,
            content_type=file.content_type,
        )

        # Process with LangGraph using BYTES (not URL)
        result = run_langgraph_on_bytes(file_content)

        # Store the generated tags in the Redis cache
        await cache_service.set_cached_tags(image_hash, result.get("persian", {}))

        # Queue database save as background task (non-blocking)
        if background_tasks:
            background_tasks.add_task(save_request_response, image_url, result)

        return {
            "image_url": image_url,
            "tags": result.get("persian", {}),
        }

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing upload: {str(e)}"
        )
