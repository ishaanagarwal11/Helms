# main.py

from fastapi import FastAPI
import uvicorn
import logging

# Import configuration and our API routes from handlers
import config
from handler import router as api_router

# Create a FastAPI app instance
app = FastAPI(
    title="Kubernetes Cluster Doctor Bridge",
    description="A bridge to access Kubernetes logs, events, and more for LLM-based cluster diagnosis.",
    version="1.0.0"
)

# Include API routes from handlers with a common prefix
app.include_router(api_router, prefix="/api")

# Define a simple root endpoint for a quick health check
@app.get("/")
async def root():
    return {"message": "Cluster Doctor Bridge API is running."}

# Main entry point to run the server
if __name__ == "__main__":
    # Setup basic logging configuration
    logging.basicConfig(level=logging.INFO)
    
    # Start the server on host and port from config.py
    uvicorn.run("main:app", host=config.SERVER_HOST, port=config.SERVER_PORT, reload=True)
