"""Custom exceptions and error payload helpers."""

from __future__ import annotations

import uuid
from http import HTTPStatus
from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ErrorPayload(BaseModel):
    """結構化錯誤回應 schema."""

    code: str = Field(..., description="機器可讀的錯誤碼")
    message: str = Field(..., description="用戶友善的錯誤訊息")
    reason: Optional[str] = Field(default=None, description="詳細原因説明")
    trace_id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="追蹤 ID")
    playlist_id: Optional[str] = Field(default=None, description="相關播放列表 ID（如適用）")
    status: int = Field(..., description="HTTP 狀態碼")

    def to_dict(self) -> Dict[str, Any]:
        """Convert to response dict."""
        return {k: v for k, v in self.dict().items() if v is not None}


class AppError(Exception):
    """Base application error carrying HTTP and machine-readable code."""

    def __init__(
        self,
        message: str,
        error_code: str,
        status_code: int,
        reason: Optional[str] = None,
        playlist_id: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.reason = reason
        self.playlist_id = playlist_id

    def to_response(self) -> Dict[str, Any]:
        """Build structured error response."""
        payload = ErrorPayload(
            code=self.error_code,
            message=self.message,
            reason=self.reason,
            status=self.status_code,
            playlist_id=self.playlist_id,
        )
        return payload.to_dict()


class InvalidParameterError(AppError):
    def __init__(
        self,
        message: str,
        error_code: str = "INVALID_PARAMETER",
        reason: Optional[str] = None,
    ) -> None:
        super().__init__(message, error_code, HTTPStatus.BAD_REQUEST, reason=reason)


class MissingParameterError(AppError):
    def __init__(
        self,
        message: str,
        error_code: str = "MISSING_PARAMETER",
        reason: Optional[str] = None,
    ) -> None:
        super().__init__(message, error_code, HTTPStatus.BAD_REQUEST, reason=reason)


class PlaylistNotFoundError(AppError):
    """播放列表不存在（404）。"""

    def __init__(
        self,
        message: str = "播放列表不存在",
        playlist_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> None:
        super().__init__(
            message,
            "PLAYLIST_NOT_FOUND",
            HTTPStatus.NOT_FOUND,
            reason=reason,
            playlist_id=playlist_id,
        )


class PlaylistForbiddenError(AppError):
    """播放列表無法存取，通常為私密或受限（403）。"""

    def __init__(
        self,
        message: str = "播放列表私密或無法存取",
        playlist_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> None:
        super().__init__(
            message,
            "PLAYLIST_FORBIDDEN",
            HTTPStatus.FORBIDDEN,
            reason=reason,
            playlist_id=playlist_id,
        )


class PlaylistGoneError(AppError):
    """播放列表已刪除或不再可用（410）。"""

    def __init__(
        self,
        message: str = "播放列表已刪除",
        playlist_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> None:
        super().__init__(
            message,
            "PLAYLIST_GONE",
            HTTPStatus.GONE,
            reason=reason,
            playlist_id=playlist_id,
        )


class PlaylistScrapingError(AppError):
    """播放列表爬取或解析失敗（502）。"""

    def __init__(
        self,
        message: str = "無法從 YouTube 提取播放列表資料",
        playlist_id: Optional[str] = None,
        reason: Optional[str] = None,
    ) -> None:
        super().__init__(
            message,
            "PLAYLIST_SCRAPING_ERROR",
            HTTPStatus.BAD_GATEWAY,
            reason=reason,
            playlist_id=playlist_id,
        )


class YouTubeUnavailableError(AppError):
    def __init__(self, message: str = "YouTube 搜尋服務暫時無法連接") -> None:
        super().__init__(message, "YOUTUBE_UNAVAILABLE", HTTPStatus.SERVICE_UNAVAILABLE)


class CacheUnavailableError(AppError):
    def __init__(self, message: str = "快取服務不可用") -> None:
        super().__init__(message, "CACHE_UNAVAILABLE", HTTPStatus.SERVICE_UNAVAILABLE)


class InternalServerError(AppError):
    def __init__(self, message: str = "內部服務錯誤") -> None:
        super().__init__(message, "INTERNAL_ERROR", HTTPStatus.INTERNAL_SERVER_ERROR)
