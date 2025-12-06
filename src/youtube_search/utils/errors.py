"""Custom exceptions and error payload helpers."""

from __future__ import annotations

from http import HTTPStatus
from typing import Dict


class AppError(Exception):
    """Base application error carrying HTTP and machine-readable code."""

    def __init__(self, message: str, error_code: str, status_code: int) -> None:
        super().__init__(message)
        self.error_code = error_code
        self.status_code = status_code

    def to_response(self) -> Dict[str, str]:
        return {"error": str(self), "error_code": self.error_code}


class InvalidParameterError(AppError):
    def __init__(self, message: str, error_code: str = "INVALID_PARAMETER") -> None:
        super().__init__(message, error_code, HTTPStatus.BAD_REQUEST)


class MissingParameterError(AppError):
    def __init__(self, message: str, error_code: str = "MISSING_PARAMETER") -> None:
        super().__init__(message, error_code, HTTPStatus.BAD_REQUEST)


class YouTubeUnavailableError(AppError):
    def __init__(self, message: str = "YouTube 搜尋服務暫時無法連接") -> None:
        super().__init__(message, "YOUTUBE_UNAVAILABLE", HTTPStatus.SERVICE_UNAVAILABLE)


class CacheUnavailableError(AppError):
    def __init__(self, message: str = "快取服務不可用") -> None:
        super().__init__(message, "CACHE_UNAVAILABLE", HTTPStatus.SERVICE_UNAVAILABLE)


class InternalServerError(AppError):
    def __init__(self, message: str = "內部服務錯誤") -> None:
        super().__init__(message, "INTERNAL_ERROR", HTTPStatus.INTERNAL_SERVER_ERROR)
