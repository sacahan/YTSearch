"""Redis caching layer for search results."""

from __future__ import annotations

import hashlib
import json
from typing import Optional

import redis

from youtube_search.config import get_settings
from youtube_search.models.search import SearchResult
from youtube_search.utils.logger import get_logger

logger = get_logger(__name__)


class CacheService:
    """Manage Redis caching for search results."""

    def __init__(self, redis_client: Optional[redis.Redis] = None) -> None:
        settings = get_settings()
        if redis_client:
            self.client = redis_client
        elif settings.redis_enabled:
            try:
                self.client = redis.Redis(
                    host=settings.redis_host,
                    port=settings.redis_port,
                    db=settings.redis_db,
                    password=settings.redis_password,
                    decode_responses=True,
                    socket_connect_timeout=2,
                    socket_timeout=2,
                )
                # Test connection
                self.client.ping()
            except (redis.RedisError, OSError) as exc:  # pragma: no cover
                logger.warning("Redis connection failed", extra={"error": str(exc)})
                self.client = None
        else:
            self.client = None
        self.ttl = settings.redis_ttl_seconds

    def get(self, keyword: str) -> Optional[SearchResult]:
        """Retrieve cached search result for keyword."""

        if not self.client:
            return None

        cache_key = self._generate_key(keyword)
        try:
            cached = self.client.get(cache_key)
            if cached:
                logger.debug("Cache hit", extra={"keyword": keyword})
                data = json.loads(cached)
                return SearchResult(**data)
        except (redis.RedisError, json.JSONDecodeError) as exc:  # pragma: no cover
            logger.warning("Cache retrieval failed", extra={"error": str(exc)})
        return None

    def set(self, keyword: str, result: SearchResult) -> None:
        """Store search result in cache with TTL."""

        if not self.client:
            return

        cache_key = self._generate_key(keyword)
        try:
            serialized = result.model_dump_json()
            self.client.setex(cache_key, self.ttl, serialized)
            logger.debug("Cache set", extra={"keyword": keyword, "ttl": self.ttl})
        except redis.RedisError as exc:  # pragma: no cover
            logger.warning("Cache storage failed", extra={"error": str(exc)})

    @staticmethod
    def _generate_key(keyword: str) -> str:
        """Generate SHA256 hash-based cache key."""

        hash_obj = hashlib.sha256(keyword.encode("utf-8"))
        return f"youtube_search:{hash_obj.hexdigest()}"


_cache_service: Optional[CacheService] = None


def get_cache_service() -> CacheService:
    """Return singleton cache service instance."""

    global _cache_service
    if _cache_service is None:
        _cache_service = CacheService()
    return _cache_service
