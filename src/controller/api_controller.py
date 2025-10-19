"""API controller for the Torob image tagging service.

This module defines the FastAPI application and all API endpoints for image analysis
and tag generation. It handles HTTP requests, validation, CORS configuration,
and integrates with the LangGraph service for image processing.
"""

from typing import Dict, Any
from fastapi import FastAPI, Body, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from prometheus_fastapi_instrumentator import Instrumentator
from dotenv import load_dotenv

from src.service.langgraph.langgraph_service import run_langgraph_on_url
from src.config.settings import APP_NAME, APP_VERSION, DEBUG_MODE


# Load environment variables from project root
load_dotenv()

# Initialize FastAPI application with metadata
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="AI-powered image analysis and tagging service for e-commerce products",
    debug=DEBUG_MODE
)

# Configure Prometheus monitoring
# Adds metrics collection and exposes /metrics endpoint for monitoring
Instrumentator().instrument(app).expose(app)


def configure_cors() -> None:
    """Configure Cross-Origin Resource Sharing (CORS) settings.
    
    Sets up CORS middleware to allow frontend applications to communicate
    with the API from different origins during development.
    """
    # Define allowed origins for CORS
    allowed_origins = [
        "http://localhost:3000",    # React development server
        "http://127.0.0.1:3000",   # Alternative localhost
        "http://localhost:3001",    # Alternative React port
        "http://127.0.0.1:3001",   # Alternative localhost
    ]
    
    # Add CORS middleware with comprehensive permissions
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,      # Specific origins allowed
        allow_credentials=True,             # Allow cookies and credentials
        allow_methods=["*"],               # Allow all HTTP methods
        allow_headers=["*"],               # Allow all headers
    )


# Configure CORS on application startup
configure_cors()


@app.get(
    "/health",
    summary="Health check endpoint",
    description="Returns the current health status of the API service",
    response_description="Service health status",
    tags=["Health"]
)
async def health_check() -> Dict[str, str]:
    """Health check endpoint for service monitoring.
    
    This endpoint provides a simple way to verify that the API service
    is running and responsive. Used by load balancers and monitoring
    systems to check service availability.
    
    Returns:
        Dict[str, str]: Health status information
        
    Example:
        GET /health
        Response: {"status": "ok", "service": "Torob API", "version": "1.0.0"}
    """
    return {
        "status": "ok",
        "service": APP_NAME,
        "version": APP_VERSION
    }


@app.post(
    "/generate-tags",
    summary="Generate tags for product image",
    description="Analyze a product image and generate relevant tags and attributes",
    response_description="Generated tags and attributes in Persian",
    tags=["Image Analysis"]
)
async def generate_tags(payload: dict = Body(...)) -> Dict[str, Any]:
    """Generate tags and attributes for a product image.
    
    This endpoint accepts an image URL, processes the image using AI models,
    and returns structured tags and attributes suitable for e-commerce
    product categorization.
    
    Args:
        payload: Request body containing image URL and optional parameters
        
    Returns:
        Dict[str, Any]: Generated tags and attributes in Persian
        
    Raises:
        HTTPException: If image_url is missing or processing fails
        
    Example:
        POST /generate-tags
        Body: {"image_url": "https://example.com/product.jpg"}
        Response: {
            "entities": [
                {"name": "جنس", "values": ["پنبه"]},
                {"name": "رنگ", "values": ["آبی"]}
            ]
        }
    """
    try:
        # Validate required parameters
        image_url = payload.get("image_url")
        if not image_url:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="image_url is required in request body"
            )
        
        # Validate URL format (basic validation)
        if not isinstance(image_url, str) or not image_url.startswith(("http://", "https://")):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="image_url must be a valid HTTP/HTTPS URL"
            )
        
        # Process image using LangGraph service
        result = run_langgraph_on_url(image_url)
        
        # Validate result structure
        if not isinstance(result, dict):
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Invalid response format from image processing service"
            )
        
        # Extract Persian results (main output format)
        persian_result = result.get("persian", {})
        
        # Ensure we have a valid response
        if not persian_result:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="No results generated for the provided image"
            )
        
        return persian_result
        
    except HTTPException:
        # Re-raise HTTP exceptions as-is
        raise
        
    except Exception as e:
        # Handle unexpected errors
        error_message = f"Unexpected error during image processing: {str(e)}"
        
        # Log error if in debug mode
        if DEBUG_MODE:
            import traceback
            print(f"Error in generate_tags: {error_message}")
            print(traceback.format_exc())
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_message
        )


@app.get(
    "/",
    summary="API information",
    description="Get basic information about the API service",
    tags=["Information"]
)
async def root() -> Dict[str, Any]:
    """Root endpoint providing API information.
    
    Returns basic information about the API service including
    name, version, and available endpoints.
    
    Returns:
        Dict[str, Any]: API service information
    """
    return {
        "service": APP_NAME,
        "version": APP_VERSION,
        "description": "AI-powered image analysis and tagging service for e-commerce products",
        "endpoints": {
            "health": "/health",
            "generate_tags": "/generate-tags",
            "docs": "/docs",
            "metrics": "/metrics"
        }
    }


# Exception handlers for better error responses
@app.exception_handler(404)
async def not_found_handler(request, exc):
    """Custom handler for 404 Not Found errors."""
    return JSONResponse(
        status_code=404,
        content={
            "error": "Endpoint not found",
            "message": f"The requested endpoint {request.url.path} does not exist",
            "available_endpoints": ["/", "/health", "/generate-tags", "/docs"]
        }
    )


@app.exception_handler(500)
async def internal_server_error_handler(request, exc):
    """Custom handler for 500 Internal Server Error."""
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal server error",
            "message": "An unexpected error occurred while processing your request"
        }
    )
