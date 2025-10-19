"""Main application entry point for the Torob project.

This module serves as the primary entry point for the FastAPI application,
handling server initialization, environment configuration, and application startup.
It loads environment variables and starts the uvicorn server with the configured
API controller.
"""

import os
import uvicorn
from dotenv import load_dotenv
from src.controller.api_controller import app


def configure_environment() -> None:
    """Configure environment variables by loading .env file.
    
    Loads environment variables from the project root .env file if it exists.
    This allows for flexible configuration across different deployment environments.
    """
    # Calculate path to project root .env file
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
    env_path = os.path.join(project_root, ".env")
    
    # Load environment variables
    load_dotenv(dotenv_path=env_path)


def start_server() -> None:
    """Start the uvicorn server with configured parameters.
    
    Initializes and starts the FastAPI application server using uvicorn
    with default host and port settings. The server will be accessible
    on all network interfaces (0.0.0.0) on port 8000.
    """
    # Configure server parameters
    host = "0.0.0.0"  # Accept connections from any IP
    port = 8000       # Default development port
    
    # Start the uvicorn server
    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    """Application entry point when run directly.
    
    This block executes when the script is run directly (not imported).
    It configures the environment and starts the server.
    """
    # Load environment configuration
    configure_environment()
    
    # Start the application server
    start_server()
