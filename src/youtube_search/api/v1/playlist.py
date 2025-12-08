"""API route definitions for playlist metadata endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from youtube_search.models.playlist import Playlist
from youtube_search.services.playlist import PlaylistService, get_playlist_service
from youtube_search.utils.errors import AppError
from youtube_search.utils.logger import get_logger

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v1", tags=["playlist"])


@router.get(
    "/playlist/metadata",
    response_model=Playlist,
    summary="取得播放列表元數據",
    response_model_exclude_none=True,
)
async def get_playlist_metadata(
    playlist_url: str = Query(
        ..., min_length=10, description="YouTube 播放列表 URL（需包含 list 參數）"
    ),
    force_refresh: bool = Query(False, description="是否強制重新取得（略過快取）"),
    service: PlaylistService = Depends(get_playlist_service),
) -> Playlist:
    """Handle GET /api/v1/playlist/metadata requests.

    For MVP (US1):
    - Validates playlist URL and extracts playlist_id
    - Returns basic metadata: playlist_id, title (if available), video_count
    - Does NOT fetch individual tracks (deferred to US2)

    Args:
        playlist_url: YouTube playlist URL containing list parameter
        force_refresh: Force refresh from YouTube (skip cache)
        service: PlaylistService dependency

    Returns:
        Playlist model with basic metadata

    Error Responses:
        400: Invalid URL format (missing list parameter, invalid domain)
        403: Playlist is private or restricted
        404: Playlist not found or does not exist
        410: Playlist has been deleted
        502: Error scraping from YouTube
    """
    try:
        logger.debug(
            f"GET /playlist/metadata: playlist_url={playlist_url}, force_refresh={force_refresh}"
        )
        return await service.get_playlist_metadata(
            playlist_url=playlist_url, force_refresh=force_refresh
        )
    except AppError as exc:
        error_payload = exc.to_response()
        logger.warning(
            f"AppError: {exc.error_code} - {str(exc)}",
            extra={"error_code": exc.error_code, "trace_id": error_payload.get("trace_id")},
        )
        return JSONResponse(status_code=exc.status_code, content=error_payload)
    except Exception as exc:  # pragma: no cover - unexpected failures
        logger.error(f"Unexpected error in /playlist/metadata: {str(exc)}", exc_info=True)
        raise HTTPException(status_code=500, detail={"error": "內部服務錯誤"}) from exc
