"""Search coordination service combining scraper, validation, and models."""

from __future__ import annotations

from typing import Optional

import anyio

from youtube_search.models.search import SearchResult
from youtube_search.services.cache import CacheService, get_cache_service
from youtube_search.services.normalizer import MetadataNormalizer, get_normalizer
from youtube_search.services.scraper import YouTubeScraper, get_scraper
from youtube_search.services.sorter import VideoSorter, get_sorter
from youtube_search.utils.validators import (
    validate_keyword,
    validate_limit,
    validate_sort_by,
)


class SearchService:
    """Orchestrates search operations using a scraper and validation layer."""

    def __init__(
        self,
        scraper: Optional[YouTubeScraper] = None,
        normalizer: Optional[MetadataNormalizer] = None,
        sorter: Optional[VideoSorter] = None,
        cache: Optional[CacheService] = None,
    ) -> None:
        self.scraper = scraper or get_scraper()
        self.normalizer = normalizer or get_normalizer()
        self.sorter = sorter or get_sorter()
        self.cache = cache or get_cache_service()

    async def search(
        self, keyword: str, limit: Optional[int] = None, sort_by: Optional[str] = None
    ) -> SearchResult:
        """Perform search and return a SearchResult model."""

        validated_keyword = validate_keyword(keyword)
        validated_limit = validate_limit(limit)
        validated_sort = validate_sort_by(sort_by)

        # Check cache first
        cached_result = self.cache.get(validated_keyword)
        if cached_result:
            # Apply limit/sort to cached results
            sorted_videos = self.sorter.sort(cached_result.videos, validated_sort)
            limited_videos = sorted_videos[:validated_limit]
            return SearchResult(
                search_keyword=validated_keyword,
                videos=limited_videos,
                result_count=len(limited_videos),
            )

        # Cache miss - fetch from YouTube
        videos = await anyio.to_thread.run_sync(self.scraper.search, validated_keyword)

        # Normalize metadata for consistency
        normalized_videos = [self.normalizer.normalize_video(v) for v in videos]

        # Store full result in cache (before limit/sort)
        full_result = SearchResult(
            search_keyword=validated_keyword,
            videos=normalized_videos,
            result_count=len(normalized_videos),
        )
        self.cache.set(validated_keyword, full_result)

        # Apply sorting and limiting
        sorted_videos = self.sorter.sort(normalized_videos, validated_sort)
        limited_videos = sorted_videos[:validated_limit]
        return SearchResult(
            search_keyword=validated_keyword,
            videos=limited_videos,
            result_count=len(limited_videos),
        )


_service: Optional[SearchService] = None


def get_search_service() -> SearchService:
    """Provide a singleton-ish SearchService instance."""

    global _service
    if _service is None:
        _service = SearchService()
    return _service
