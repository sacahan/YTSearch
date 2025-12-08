"""API route definitions for v1 search endpoint."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse

from youtube_search.models.search import SearchResult
from youtube_search.services.search import SearchService, get_search_service
from youtube_search.utils.errors import AppError

router = APIRouter(prefix="/api/v1", tags=["search"])


@router.get(
    "/search",
    response_model=SearchResult,
    summary="搜尋 YouTube 影片",
    response_model_exclude_none=True,
    responses={
        200: {
            "description": "成功返回搜尋結果",
            "content": {
                "application/json": {
                    "example": {
                        "search_keyword": "Python教學",
                        "result_count": 10,
                        "videos": [
                            {
                                "video_id": "dQw4w9WgXcQ",
                                "title": "Python Tutorial for Beginners",
                                "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
                                "channel": "Corey Schafer",
                                "channel_url": "https://www.youtube.com/channel/UCxxxxx",
                                "publish_date": "3 years ago",
                                "view_count": 5000000,
                                "description": "Complete Python tutorial covering basics...",
                            }
                        ],
                    }
                }
            },
        },
        400: {
            "description": "無效的搜尋參數",
            "content": {
                "application/json": {
                    "example": {
                        "error": "keyword 為必須參數",
                        "error_code": "MISSING_PARAMETER",
                    }
                }
            },
        },
        503: {
            "description": "YouTube 服務不可用",
            "content": {
                "application/json": {
                    "example": {
                        "error": "YouTube 搜尋服務暫時無法連接",
                        "error_code": "YOUTUBE_UNAVAILABLE",
                    }
                }
            },
        },
    },
)
async def search_videos(
    keyword: str = Query(..., min_length=1, max_length=200, description="搜尋關鍵字"),
    limit: int = Query(1, ge=1, le=100, description="返回結果數量，預設 1"),
    sort_by: str = Query(
        "relevance", pattern="^(relevance|date)$", description="排序方式,預設 relevance"
    ),
    service: SearchService = Depends(get_search_service),
) -> SearchResult:
    """Handle GET /api/v1/search requests."""

    try:
        return await service.search(keyword=keyword, limit=limit, sort_by=sort_by)
    except AppError as exc:
        return JSONResponse(status_code=exc.status_code, content=exc.to_response())
    except Exception as exc:  # pragma: no cover - unexpected failures
        raise HTTPException(status_code=500, detail={"error": str(exc)}) from exc
