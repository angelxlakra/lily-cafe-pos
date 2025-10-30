"""
Main FastAPI application for Lily Cafe POS System.
Entry point for the API.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import init_db

# Create FastAPI application
app = FastAPI(
    title="Lily Cafe POS API",
    description="Point of Sale system for Lily Cafe by Mary's Kitchen",
    version="0.1.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================================
# Startup Event
# ============================================================================


@app.on_event("startup")
def startup_event():
    """Initialize database on application startup."""
    init_db()


# ============================================================================
# Health Check Routes
# ============================================================================


@app.get("/")
def root():
    """Root endpoint for health check."""
    return {
        "message": "Lily Cafe POS API",
        "version": "0.1.0",
        "status": "running",
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# ============================================================================
# Include API Router
# ============================================================================

app.include_router(api_router, prefix="/api/v1")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
