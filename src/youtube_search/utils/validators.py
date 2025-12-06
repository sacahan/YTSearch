"""Input validation utilities for API parameters."""

from __future__ import annotations

from typing import Literal, Optional

from youtube_search.utils.errors import InvalidParameterError, MissingParameterError


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
