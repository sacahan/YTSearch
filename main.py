"""FastAPI application entrypoint for YouTube Search API."""

from __future__ import annotations

from fastapi import FastAPI

from youtube_search.api.v1.search import router as search_router
from youtube_search.utils.logger import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

app = FastAPI(title="YouTube 搜尋 API", version="1.0.0")
app.include_router(search_router)


@app.get("/health", tags=["health"])
def health() -> dict[str, str]:
    """Simple health check endpoint."""

    logger.debug("health check")
    return {"status": "ok"}


if __name__ == "__main__":  # pragma: no cover
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
