"""FastAPI application entrypoint for YouTube Search API."""

from __future__ import annotations

from fastapi import FastAPI

from youtube_search.api.v1.docs import router as docs_router
from youtube_search.api.v1.playlist import router as playlist_router
from youtube_search.api.v1.search import router as search_router
from youtube_search.mcp.router import router as mcp_router
from youtube_search.services.cache import get_cache_service
from youtube_search.utils.logger import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

app = FastAPI(
    title="YouTube 搜尋 API",
    version="1.0.0",
    description="提供 YouTube 搜尋與播放列表元數據提取的 REST API 服務",
    docs_url="/api/docs",
    openapi_url="/api/openapi.json",
    redoc_url="/api/redoc",
)
app.include_router(docs_router)
app.include_router(search_router)
app.include_router(playlist_router)
app.include_router(mcp_router)


@app.on_event("startup")
async def startup_event() -> None:
    """Initialize services on application startup."""

    logger.info("Starting YouTube Search API...")

    # Initialize and test Redis connection
    cache_service = get_cache_service()
    if cache_service.client:
        logger.info("Redis cache service initialized and ready")
    else:
        logger.warning("Running without Redis cache - all searches will be live")

    # Initialize MCP server
    try:
        from youtube_search.mcp.server import get_mcp_server_manager  # noqa: F401
        get_mcp_server_manager()
        logger.info("MCP server initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize MCP server: {str(e)}", exc_info=True)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Simple health check endpoint."""

    logger.debug("health check")
    return {"status": "ok"}


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
