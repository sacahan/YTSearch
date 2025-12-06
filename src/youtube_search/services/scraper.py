"""YouTube search page scraper using requests and ytInitialData extraction."""

from __future__ import annotations

import json
import re
from typing import Any, Dict, Iterable, List

import requests

from youtube_search.config import get_settings
from youtube_search.models.video import Video
from youtube_search.utils.errors import YouTubeUnavailableError
from youtube_search.utils.logger import get_logger

logger = get_logger(__name__)


class YouTubeScraper:
    """Scrape YouTube search result pages to extract video metadata."""

    def __init__(self) -> None:
        self.settings = get_settings()
        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": (
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/118.0.0.0 Safari/537.36"
                )
            }
        )

    def search(self, keyword: str) -> List[Video]:
        """Fetch search results and return a list of Video models."""

        params = {"search_query": keyword, "q": keyword, "hl": "en"}
        try:
            response = self.session.get(
                self.settings.youtube_base_url,
                params=params,
                timeout=self.settings.youtube_timeout,
            )
            response.raise_for_status()
        except (
            requests.RequestException
        ) as exc:  # pragma: no cover - network exception path
            logger.warning("YouTube request failed", extra={"error": str(exc)})
            raise YouTubeUnavailableError()

        return self._extract_videos(response.text)

    def _extract_videos(self, html: str) -> List[Video]:
        """Parse HTML to extract video renderers and map to Video models."""

        data = self._extract_ytinitialdata(html)
        renderers = list(self._iter_video_renderers(data))
        videos: List[Video] = []
        for renderer in renderers:
            video_id = renderer.get("videoId")
            if not video_id:
                continue

            # Extract all available metadata fields
            title = self._get_text(renderer.get("title"))
            channel = self._get_text(renderer.get("ownerText"))
            channel_url = self._extract_channel_url(renderer.get("ownerText"))
            publish_date = self._extract_publish_date(renderer.get("publishedTimeText"))
            view_count = self._extract_view_count(renderer.get("viewCountText"))
            description = (
                self._get_text(
                    renderer.get("detailedMetadataSnippets", [{}])[0].get("snippetText")
                )
                if renderer.get("detailedMetadataSnippets")
                else None
            )

            videos.append(
                Video(
                    video_id=video_id,
                    title=title,
                    url=Video.build_url(video_id),
                    channel=channel,
                    channel_url=channel_url,
                    publish_date=publish_date,
                    view_count=view_count,
                    description=description,
                )
            )
        return videos

    def _extract_ytinitialdata(self, html: str) -> Dict[str, Any]:
        """Extract ytInitialData JSON blob from HTML."""

        match = re.search(r"ytInitialData" + r"\s*=\s*(\{.*?\})\s*;\s*", html, re.S)
        if not match:
            logger.warning("ytInitialData not found in HTML")
            return {}
        json_str = match.group(1)
        try:
            return json.loads(json_str)
        except json.JSONDecodeError as exc:  # pragma: no cover - malformed HTML path
            logger.warning("Failed to parse ytInitialData", extra={"error": str(exc)})
            return {}

    def _iter_video_renderers(self, data: Any) -> Iterable[Dict[str, Any]]:
        """Recursively yield videoRenderer dicts from the JSON structure."""

        if isinstance(data, dict):
            if "videoRenderer" in data:
                yield data["videoRenderer"]
            for value in data.values():
                yield from self._iter_video_renderers(value)
        elif isinstance(data, list):
            for item in data:
                yield from self._iter_video_renderers(item)

    @staticmethod
    def _get_text(node: Any) -> str | None:
        """Extract simple text content from YouTube renderer node."""

        if not isinstance(node, dict):
            return None
        runs = node.get("runs")
        if isinstance(runs, list) and runs:
            text = runs[0].get("text")
            return text.strip() if isinstance(text, str) else None
        return None

    @staticmethod
    def _extract_channel_url(node: Any) -> str | None:
        """Extract channel URL from ownerText navigation endpoint."""

        if not isinstance(node, dict):
            return None
        runs = node.get("runs")
        if isinstance(runs, list) and runs:
            endpoint = runs[0].get("navigationEndpoint", {})
            browse_endpoint = endpoint.get("browseEndpoint", {})
            canonical_base = browse_endpoint.get("canonicalBaseUrl")
            if canonical_base:
                return f"https://www.youtube.com{canonical_base}"
        return None

    @staticmethod
    def _extract_publish_date(node: Any) -> str | None:
        """Extract and normalize publish date to ISO 8601 format (best effort)."""

        # YouTube provides relative time ("2 days ago"), not ISO timestamps.
        # For POC, we store the simple text; full date parsing deferred.
        text = YouTubeScraper._get_text(node)
        if text:
            # Store as-is for now; normalizer can convert if needed
            return text
        return None

    @staticmethod
    def _extract_view_count(node: Any) -> int | None:
        """Extract view count from viewCountText."""

        text = YouTubeScraper._get_text(node)
        if not text:
            return None
        # Parse view count from text like "1.2M views" or "1,234 views"

        match = re.search(r"([\d,\.]+)\s*([KMB])?\s*view", text, re.I)
        if not match:
            return None
        num_str = match.group(1).replace(",", "")
        multiplier_str = match.group(2)
        try:
            num = float(num_str)
            if multiplier_str:
                multipliers = {"K": 1_000, "M": 1_000_000, "B": 1_000_000_000}
                num *= multipliers.get(multiplier_str.upper(), 1)
            return int(num)
        except (ValueError, TypeError):
            return None


def get_scraper() -> YouTubeScraper:
    """Factory to obtain a scraper instance (simple singleton via module import)."""

    return YouTubeScraper()
