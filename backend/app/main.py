"""
Main FastAPI application for Lily Cafe POS System.
Entry point for the API.
"""

from contextlib import AsyncExitStack, asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.v1.router import api_router
from app.core.config import settings
from app.db.session import init_db
from app.version import __version__, get_build_info, get_version_info


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize the database and settings cache, then run for the app's life."""
    init_db()
    # Load settings from DB into the in-memory cache.
    # init_db() runs first so the app_settings table is guaranteed to exist.
    from app.core import settings_store
    from app.db.session import SessionLocal
    db = SessionLocal()
    try:
        settings_store.load(db)
    finally:
        db.close()

    async with AsyncExitStack() as stack:
        if settings.MCP_ENABLED:
            # The MCP app is mounted as a sub-application, and Starlette only
            # runs the root app's lifespan, so its session manager has to be
            # started from here or every /mcp request fails.
            from app.mcp.server import mcp
            await stack.enter_async_context(mcp.session_manager.run())

        # The morning digest runs in-process: this app never sleeps
        # (fly.toml pins min_machines_running = 1), so a daily job needs a
        # sleeping task, not a scheduler library or a second machine.
        from app.ask import scheduler
        digest_task = scheduler.start(app)
        try:
            yield
        finally:
            if digest_task is not None:
                digest_task.cancel()


# Create FastAPI application
app = FastAPI(
    title="Lily Cafe POS API",
    description="Point of Sale system for Lily Cafe by Mary's Kitchen",
    version=__version__,
    lifespan=lifespan,
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
# Health Check Routes
# ============================================================================


@app.get("/")
def root():
    """Root endpoint for health check."""
    return {
        "message": "Lily Cafe POS API",
        "version": __version__,
        "status": "running",
        **get_build_info(),
    }


@app.get("/version")
def version_info():
    """Get detailed version information."""
    return get_version_info()


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


# ============================================================================
# Include API Router
# ============================================================================

app.include_router(api_router, prefix="/api/v1")


# ============================================================================
# MCP server (opt-in)
# ============================================================================

if settings.MCP_ENABLED:
    from app.mcp.server import create_mcp_http_app, mcp

    # Mounted at the origin root, and last: OAuth discovery lives at
    # /.well-known/... on the bare host, and everything registered above
    # keeps precedence over the mount.
    app.mount("/", create_mcp_http_app(mcp))


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
