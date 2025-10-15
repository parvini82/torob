from src.controller.api_controller import app
import uvicorn
from dotenv import load_dotenv
import os

if __name__ == "__main__":
    # Load .env from project root if present
    load_dotenv(dotenv_path=os.path.join(os.path.dirname(os.path.dirname(__file__)), "..", ".env"))
    uvicorn.run(app, host="0.0.0.0", port=8000)
