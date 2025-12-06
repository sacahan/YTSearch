"""Integration tests for Redis caching."""

from unittest.mock import MagicMock

from youtube_search.models.search import SearchResult
from youtube_search.models.video import Video
from youtube_search.services.cache import CacheService


def test_cache_get_returns_none_when_disabled():
    """Verify cache gracefully returns None when Redis disabled."""
    cache = CacheService(redis_client=None)
    result = cache.get("test")
    assert result is None


def test_cache_set_does_nothing_when_disabled():
    """Verify cache.set doesn't crash when Redis disabled."""
    cache = CacheService(redis_client=None)
    result = SearchResult(search_keyword="test", videos=[], result_count=0)
    cache.set("test", result)  # Should not raise


def test_cache_roundtrip_with_mock_redis():
    """Verify cache can store and retrieve SearchResult."""
    mock_redis = MagicMock()
    cache = CacheService(redis_client=mock_redis)

    video = Video(video_id="test1234567", title="Test Video")
    result = SearchResult(search_keyword="Python", videos=[video], result_count=1)

    # Mock setex to store data
    stored_data = {}

    def mock_setex(key, ttl, value):
        stored_data[key] = value

    def mock_get(key):
        return stored_data.get(key)

    mock_redis.setex = mock_setex
    mock_redis.get = mock_get

    cache.set("Python", result)
    cached = cache.get("Python")

    assert cached is not None
    assert cached.search_keyword == "Python"
    assert cached.result_count == 1
    assert cached.videos[0].video_id == "test1234567"


def test_cache_key_generation_is_deterministic():
    """Verify cache key is consistent for same keyword."""
    key1 = CacheService._generate_key("Python教學")
    key2 = CacheService._generate_key("Python教學")
    assert key1 == key2
    assert key1.startswith("youtube_search:")


def test_cache_key_generation_differs_for_different_keywords():
    """Verify different keywords generate different cache keys."""
    key1 = CacheService._generate_key("Python")
    key2 = CacheService._generate_key("JavaScript")
    assert key1 != key2
