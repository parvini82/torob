import os
from fastapi import BackgroundTasks, Body, FastAPI, HTTPException, Request, File, UploadFile, Query, Depends
from fastapi.security import APIKeyHeader

from src.service.database.database import save_request_response
from src.service.ratelimit.rate_limit_service import RateLimitService
from src.service.caching.redis_cache_service import RedisCacheService, get_cache_service
from src.service.langgraph.langgraph_service import run_langgraph_on_bytes, run_langgraph_on_url
from src.service.minio import get_minio_service
from fastapi.middleware.cors import CORSMiddleware
from prometheus_fastapi_instrumentator import Instrumentator
from redis import Redis
from dotenv import load_dotenv
from prometheus_client import Histogram, Counter, generate_latest
import time

# Load environment variables from .env file
load_dotenv()

# Read the list of valid API tokens from the environment (comma-separated)
API_TOKENS = os.getenv("API_TOKENS", "").split(",")

# Ensure that the API_TOKENS list is populated
if not API_TOKENS:
    raise ValueError("API_TOKENS is not set or is empty in the environment variables")

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



# Dependency to fetch API token for authentication
api_key_header = APIKeyHeader(name="Authorization", auto_error=True)

# Cache hit/miss counters
CACHE_HIT_COUNTER = Counter(
    "cache_hit_count",
    "Number of cache hits",
    ["endpoint"]
)

CACHE_MISS_COUNTER = Counter(
    "cache_miss_count",
    "Number of cache misses",
    ["endpoint"]
)
REQUEST_LATENCY = Histogram(
    "api_response_latency_seconds",
    "Response latency (seconds) for API endpoints",
    ["method", "endpoint"]
)

@app.middleware("http")
async def add_latency_metric(request: Request, call_next):
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    REQUEST_LATENCY.labels(request.method, request.url.path).observe(process_time)
    response.headers["X-Process-Time"] = f"{process_time:.3f}s"
    return response

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
    file = payload.get("file")  # Added file input handling
    mode = payload.get("mode", "fast")  # Get mode: fast, reasoning, or advanced_reasoning

    if not image_url and not file:
        return {"error": "Either 'image_url' or 'file' is required"}

    if image_url:
        # Generate the image hash for caching
        image_hash = RedisCacheService.generate_image_hash((image_url + mode).encode("utf-8"))

        # Check if the tags are already cached
        cache_service = get_cache_service()
        cached_tags = await cache_service.get_cached_tags(image_hash)

        if cached_tags:
            # If tags are cached, return them directly
            CACHE_HIT_COUNTER.labels(request.url.path).inc()  # Increment cache hit

            return cached_tags

        else:
            CACHE_MISS_COUNTER.labels(request.url.path).inc()

        try:
            # If not cached, call the LangGraph service to process the URL and get the response
            result = run_langgraph_on_url(image_url, mode=mode)

            # Store the generated tags in the Redis cache
            await cache_service.set_cached_tags(image_hash, result.get("persian", {}))

            # Queue database save as background task (non-blocking)
            if background_tasks:
                background_tasks.add_task(save_request_response, image_url, result)

            return result.get("persian", {})

        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")

    elif file:
        # Handle file upload and image processing
        return await upload_and_tag(file, background_tasks, request, mode)  # Delegating to file handler

@app.post("/upload-and-tag")
async def upload_and_tag(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = None,
    request: Request = None,  # Added request dependency for IP check
    mode: str = Query("fast", description="Processing mode: fast, reasoning, or advanced_reasoning")  # Default mode
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
        image_hash = RedisCacheService.generate_image_hash(file_content + mode.encode("utf-8"))
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
        result = run_langgraph_on_bytes(file_content, mode=mode)

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

# New external API endpoint for token-based access
@app.post("/external-generate-tags")
async def external_generate_tags(
    payload: dict = Body(...),
    background_tasks: BackgroundTasks = None,
    request: Request = None,
    api_token: str = Depends(api_key_header)
):
    # Check if the provided API token is valid (exists in the list of valid tokens)
    if api_token not in API_TOKENS:
        raise HTTPException(status_code=403, detail="Invalid or missing API token")

    # Continue with the same logic as /generate-tags
    return await generate_tags(payload, background_tasks, request)
