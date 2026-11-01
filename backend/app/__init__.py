"""
Backend application package for Flood Evacuation Route Planning.

This package contains the FastAPI application and all backend services
 for the academic flood evacuation simulation project.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="Flood Evacuation Route Planning API",
    description="Academic flood evacuation route planning simulator around Tezpur University, Assam",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# Add CORS middleware for frontend integration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "project": "Flood Evacuation Route Planning",
        "version": "1.0.0"
    }

# Import API routes
from backend.app.api.routes import router

app.include_router(router)