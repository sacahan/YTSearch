"""Input validation utilities for API parameters."""

from __future__ import annotations

import re
from typing import Literal, Optional
from urllib.parse import parse_qs, urlparse

from youtube_search.utils.errors import InvalidParameterError, MissingParameterError

_PLAYLIST_ID_PATTERN = re.compile(r"^[a-zA-Z0-9_-]{6,50}$")
_PLAYLIST_ALLOWED_DOMAINS = {
    "www.youtube.com",
    "youtube.com",
    "m.youtube.com",
    "youtu.be",
}


def validate_keyword(keyword: Optional[str]) -> str:
    """Validate keyword presence and length constraints (1-200 chars)."""

    if keyword is None or keyword.strip() == "":
        raise MissingParameterError("keyword 為必須參數")
    value = keyword.strip()
    if not (1 <= len(value) <= 200):
        raise InvalidParameterError(
            "keyword 長度必須介於 1-200 字元", "INVALID_KEYWORD_LENGTH"
        )
    return value


def validate_limit(limit: Optional[int]) -> int:
    """Validate result limit within 1-100 inclusive; default to 1 when None."""

    if limit is None:
        return 1
    if not (1 <= limit <= 100):
        raise InvalidParameterError("limit 必須在 1-100 之間", "INVALID_LIMIT")
    return limit


def validate_sort_by(sort_by: Optional[str]) -> Literal["relevance", "date"]:
    """Validate sort_by field; defaults to relevance."""

    if sort_by is None:
        return "relevance"
    value = sort_by.strip().lower()
    if value not in {"relevance", "date"}:
        raise InvalidParameterError(
            "sort_by 僅支援 relevance 或 date", "INVALID_SORT_BY"
        )
    return value  # type: ignore[return-value]


def validate_playlist_id(playlist_id: Optional[str]) -> str:
    """Validate playlist_id length and character set."""

    if playlist_id is None or playlist_id.strip() == "":
        raise MissingParameterError("playlist_id 為必須參數")

    value = playlist_id.strip()
    if not _PLAYLIST_ID_PATTERN.fullmatch(value):
        raise InvalidParameterError(
            "playlist_id 僅允許英數及 _ -，長度 6-50", "INVALID_PLAYLIST_ID"
        )
    return value


def extract_playlist_id_from_url(playlist_url: Optional[str]) -> str:
    """Extract and validate playlist_id from a YouTube playlist URL."""

    if playlist_url is None or playlist_url.strip() == "":
        raise MissingParameterError("playlist_url 為必須參數")

    normalized_url = playlist_url.strip()
    parsed = urlparse(normalized_url)

    if parsed.scheme not in {"http", "https"}:
        raise InvalidParameterError(
            "playlist_url 必須為 http 或 https", "INVALID_PLAYLIST_URL_SCHEME"
        )

    domain = parsed.netloc.lower()
    if domain not in _PLAYLIST_ALLOWED_DOMAINS:
        raise InvalidParameterError(
            "playlist_url 僅支援 youtube.com 或 youtu.be 網域",
            "INVALID_PLAYLIST_DOMAIN",
        )

    query_params = parse_qs(parsed.query)
    playlist_id = query_params.get("list", [None])[0]
    if playlist_id is None:
        raise InvalidParameterError("playlist_url 缺少 list 參數", "PLAYLIST_ID_NOT_FOUND")

    return validate_playlist_id(playlist_id)
