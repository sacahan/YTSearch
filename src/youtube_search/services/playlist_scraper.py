"""YouTube playlist scraper using requests and ytInitialData extraction with continuation."""

from __future__ import annotations

import json
import re
import time
from typing import Any, Optional

import requests

from youtube_search.config import get_settings
from youtube_search.models.playlist import Track
from youtube_search.utils.errors import PlaylistScrapingError
from youtube_search.utils.logger import get_logger

logger = get_logger(__name__)

# Configuration for long playlist handling (per research.md Phase 2 - T014a)
MAX_CONTINUATION_BATCHES = 15
MAX_TOTAL_SCRAPE_SECONDS = 30
INITIAL_REQUEST_TIMEOUT = 10
CONTINUATION_REQUEST_TIMEOUT = 5


class PlaylistScraper:
    """Scrape YouTube playlist pages to extract track metadata via ytInitialData and continuation."""

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

    def fetch_playlist(self, playlist_url: str) -> tuple[list[Track], bool, dict[str, Any]]:
        """Fetch all tracks from a YouTube playlist via URL.

        Args:
            playlist_url: Full YouTube playlist URL with list parameter

        Returns:
            Tuple of:
            - tracks: List of Track objects extracted
            - partial: True if list is incomplete due to timeout/batch limit
            - metadata: Dict with playlist title, video_count, and diagnostics

        Raises:
            PlaylistScrapingError: If initial fetch fails or URL is invalid
        """
        start_time = time.time()
        tracks: list[Track] = []
        continuation_batches = 0
        partial = False
        metadata: dict[str, Any] = {
            "title": None,
            "video_count": None,
            "continuation_batches": 0,
            "elapsed_seconds": 0,
            "fetched_track_count": 0,
            "partial_reason": None,
        }

        try:
            # Fetch initial page
            logger.debug(f"Fetching playlist page: {playlist_url}")
            response = self.session.get(playlist_url, timeout=INITIAL_REQUEST_TIMEOUT)
            response.raise_for_status()
        except requests.RequestException as exc:
            logger.error(
                f"Failed to fetch playlist URL: {str(exc)}",
                extra={"playlist_url": playlist_url},
            )
            raise PlaylistScrapingError(
                "無法連接 YouTube 播放列表頁面",
                reason=str(exc),
            )

        # Extract initial ytInitialData
        try:
            initial_data = self._extract_ytinitialdata(response.text)
        except Exception as exc:
            logger.error(f"Failed to extract ytInitialData from initial page: {str(exc)}")
            raise PlaylistScrapingError(
                "無法解析播放列表資料",
                reason="ytInitialData 提取失敗",
            )

        # Extract initial playlist metadata and tracks
        try:
            playlist_header = self._extract_playlist_header(initial_data)
            metadata["title"] = playlist_header.get("title")
            metadata["video_count"] = playlist_header.get("video_count")

            initial_tracks = self._extract_tracks_from_data(initial_data)
            tracks.extend(initial_tracks)

            continuation_token = self._extract_continuation_token(initial_data)
        except Exception as exc:
            logger.error(f"Failed to parse initial playlist data: {str(exc)}")
            raise PlaylistScrapingError(
                "無法解析播放列表內容",
                reason=str(exc),
            )

        # Iteratively fetch continuation batches
        while continuation_token and continuation_batches < MAX_CONTINUATION_BATCHES:
            elapsed = time.time() - start_time
            if elapsed > MAX_TOTAL_SCRAPE_SECONDS:
                logger.warning(
                    f"Playlist scraping exceeded {MAX_TOTAL_SCRAPE_SECONDS}s timeout",
                    extra={
                        "elapsed_seconds": elapsed,
                        "fetched_count": len(tracks),
                    },
                )
                partial = True
                metadata["partial_reason"] = "TIMEOUT"
                break

            try:
                continuation_batches += 1
                logger.debug(
                    f"Fetching continuation batch {continuation_batches}: elapsed {elapsed:.1f}s"
                )

                continuation_data = self._fetch_continuation(
                    continuation_token,
                    timeout_sec=min(
                        CONTINUATION_REQUEST_TIMEOUT,
                        MAX_TOTAL_SCRAPE_SECONDS - elapsed,
                    ),
                )
                continuation_tracks = self._extract_tracks_from_data(continuation_data)
                tracks.extend(continuation_tracks)

                # Try to get next continuation token
                new_token = self._extract_continuation_token(continuation_data)
                if not new_token:
                    logger.debug("No more continuation tokens available")
                    break
                continuation_token = new_token

            except requests.Timeout:
                logger.warning(f"Continuation request timed out at batch {continuation_batches}")
                partial = True
                metadata["partial_reason"] = "CONTINUATION_TIMEOUT"
                break
            except Exception as exc:
                logger.error(
                    f"Error processing continuation batch {continuation_batches}: {str(exc)}"
                )
                partial = True
                metadata["partial_reason"] = "CONTINUATION_ERROR"
                break

        # Check if we hit batch limit
        if continuation_batches >= MAX_CONTINUATION_BATCHES and continuation_token:
            logger.warning(f"Reached continuation batch limit ({MAX_CONTINUATION_BATCHES})")
            partial = True
            metadata["partial_reason"] = "BATCH_LIMIT_EXCEEDED"

        # Update metadata
        metadata["continuation_batches"] = continuation_batches
        metadata["elapsed_seconds"] = time.time() - start_time
        metadata["fetched_track_count"] = len(tracks)

        logger.info(
            f"Playlist scrape complete: fetched {len(tracks)} tracks, "
            f"partial={partial}, batches={continuation_batches}",
            extra=metadata,
        )

        return tracks, partial, metadata

    def _extract_ytinitialdata(self, html: str) -> dict[str, Any]:
        """Extract ytInitialData JSON from HTML response."""
        match = re.search(r"var ytInitialData = ({.*?});", html, re.DOTALL)
        if not match:
            raise PlaylistScrapingError("Unable to locate ytInitialData in playlist page")
        return json.loads(match.group(1))

    def _extract_playlist_header(self, data: dict[str, Any]) -> dict[str, Any]:
        """Extract playlist metadata from header."""
        result = {"title": None, "video_count": None}

        try:
            # Navigate to playlist header in responseContext
            header = data.get("header", {}).get("playlistHeaderRenderer", {})
            if header:
                result["title"] = self._get_text(header.get("title"))
                subtitle = self._get_text(header.get("subtitle"))
                if subtitle:
                    # Extract video count from subtitle like "100 videos"
                    match = re.search(r"(\d+)\s+video", subtitle)
                    if match:
                        result["video_count"] = int(match.group(1))
        except (KeyError, ValueError, AttributeError) as exc:
            # Some playlist pages may lack subtitle or have unexpected structure.
            # Log and continue, returning partial metadata if possible.
            logger.debug(f"Error extracting playlist header metadata: {exc}")

        return result

    def _extract_tracks_from_data(self, data: dict[str, Any]) -> list[Track]:
        """Extract track list from ytInitialData.

        Supports both:
        - Playlist pages: /playlist?list=XXX → twoColumnBrowseResultsRenderer
        - Watch pages with playlist: /watch?v=XXX&list=XXX → twoColumnWatchNextResults
        """
        tracks: list[Track] = []
        position = 0

        try:
            contents = data.get("contents", {})

            # Try watch format first (when user provides watch URL with list param)
            watch_results = contents.get("twoColumnWatchNextResults", {})
            if watch_results:
                playlist = watch_results.get("playlist", {}).get("playlist", {})
                if playlist:
                    playlist_contents = playlist.get("contents", [])
                    for item in playlist_contents:
                        if "playlistPanelVideoRenderer" in item:
                            position += 1
                            track = self._parse_playlist_panel_video_renderer(
                                item["playlistPanelVideoRenderer"],
                                position,
                            )
                            if track:
                                tracks.append(track)
                    return tracks

            # Try playlist format (twoColumnBrowseResultsRenderer)
            browse_results = contents.get("twoColumnBrowseResultsRenderer", {})
            if browse_results:
                tabs = browse_results.get("tabs", [])
                for tab in tabs:
                    if "tabRenderer" in tab:
                        contents_inner = (
                            tab["tabRenderer"]
                            .get("content", {})
                            .get("sectionListRenderer", {})
                            .get("contents", [])
                        )
                        for section in contents_inner:
                            if "itemSectionRenderer" in section:
                                renderers = section["itemSectionRenderer"].get("contents", [])
                                for renderer in renderers:
                                    if "playlistVideoRenderer" in renderer:
                                        position += 1
                                        track = self._parse_playlist_video_renderer(
                                            renderer["playlistVideoRenderer"],
                                            position,
                                        )
                                        if track:
                                            tracks.append(track)
        except (KeyError, IndexError, TypeError) as exc:
            logger.warning(f"Error parsing playlist video renderers: {str(exc)}")

        return tracks

    def _parse_playlist_video_renderer(
        self, renderer: dict[str, Any], position: int
    ) -> Optional[Track]:
        """Parse a playlistVideoRenderer to extract Track metadata."""
        try:
            video_id = renderer.get("videoId")
            if not video_id:
                return None

            title = self._get_text(renderer.get("title"))
            if not title:
                return None

            channel = self._get_text(renderer.get("shortBylineText"))
            channel_url = self._extract_channel_url(renderer.get("shortBylineText"))
            publish_date = self._extract_publish_date(renderer.get("publishedTimeText"))
            duration = self._extract_duration(renderer.get("videoDetails"))
            view_count = self._extract_view_count(renderer.get("videoDetails"))

            return Track(
                video_id=video_id,
                title=title,
                channel=channel,
                channel_url=channel_url,
                url=Track.build_url(video_id),
                publish_date=publish_date,
                duration=duration,
                view_count=view_count,
                position=position,
            )
        except (KeyError, ValueError) as exc:
            logger.debug(f"Failed to parse renderer: {str(exc)}")
            return None

    def _parse_playlist_panel_video_renderer(
        self, renderer: dict[str, Any], position: int
    ) -> Optional[Track]:
        """Parse a playlistPanelVideoRenderer to extract Track metadata.

        Used when parsing watch page playlists (/watch?v=XXX&list=XXX).
        Has different structure than playlistVideoRenderer.
        """
        try:
            video_id = renderer.get("videoId")
            if not video_id:
                return None

            title = self._get_text(renderer.get("title"))
            if not title:
                return None

            # In panel format, use longBylineText instead of shortBylineText
            channel = self._get_text(renderer.get("longBylineText"))
            channel_url = self._extract_channel_url(renderer.get("longBylineText"))

            # Extract duration from lengthText (e.g., "3:45")
            duration = self._get_text(renderer.get("lengthText"))

            # Panel format doesn't have publish_date or view_count readily available
            publish_date = None
            view_count = None

            return Track(
                video_id=video_id,
                title=title,
                channel=channel,
                channel_url=channel_url,
                url=Track.build_url(video_id),
                publish_date=publish_date,
                duration=duration,
                view_count=view_count,
                position=position,
            )
        except (KeyError, ValueError) as exc:
            logger.debug(f"Failed to parse panel renderer: {str(exc)}")
            return None

    def _extract_continuation_token(self, data: dict[str, Any]) -> Optional[str]:
        """Extract continuation token from ytInitialData or continuation response.

        Supports both:
        - Playlist format: twoColumnBrowseResultsRenderer
        - Watch format: twoColumnWatchNextResults
        """
        try:
            contents = data.get("contents", {})

            # Try watch format first (when parsing watch page with playlist)
            watch_results = contents.get("twoColumnWatchNextResults", {})
            if watch_results:
                playlist = watch_results.get("playlist", {}).get("playlist", {})
                continuations = playlist.get("continuations", [])
                if continuations:
                    return continuations[0].get("nextContinuationData", {}).get("continuation")
                return None

            # Try playlist format (twoColumnBrowseResultsRenderer)
            browse_results = contents.get("twoColumnBrowseResultsRenderer", {})
            if browse_results:
                tabs = browse_results.get("tabs", [])
                for tab in tabs:
                    if "tabRenderer" in tab:
                        contents_inner = (
                            tab["tabRenderer"]
                            .get("content", {})
                            .get("sectionListRenderer", {})
                            .get("contents", [])
                        )
                        for section in contents_inner:
                            if "itemSectionRenderer" in section:
                                continuation = section["itemSectionRenderer"].get(
                                    "continuations", []
                                )
                                if continuation:
                                    return (
                                        continuation[0]
                                        .get("nextContinuationData", {})
                                        .get("continuation")
                                    )
                return None
        except (KeyError, IndexError, TypeError) as exc:
            # We expect occasional KeyError/IndexError/TypeError due to dynamic YouTube response formats.
            # These indicate missing or unexpected data structure; treat as "no continuation token found".
            logger.debug("Failed to extract continuation token: %r", exc)

        return None

    def _fetch_continuation(
        self, continuation_token: str, timeout_sec: float = CONTINUATION_REQUEST_TIMEOUT
    ) -> dict[str, Any]:
        """Fetch continuation batch from YouTube.

        Uses the same youtube.com domain - never calls googleapis.com (per T019).
        """
        # Enforce youtube.com domain only (no googleapis.com calls)
        url = f"{self.settings.youtube_base_url}/?action_get_playlist"

        # Validate URL to ensure no googleapis calls
        if "googleapis" in url.lower():
            raise PlaylistScrapingError(
                "YouTube Data API 呼叫被禁止",
                reason="Only youtube.com web scraping is allowed",
            )

        data = {
            "context": {
                "client": {
                    "clientName": "WEB",
                    "clientVersion": "2.20240101.00.00",
                }
            },
            "continuation": continuation_token,
        }

        response = self.session.post(
            url,
            json=data,
            timeout=timeout_sec,
        )
        response.raise_for_status()

        return response.json()

    def _get_text(self, obj: Any) -> Optional[str]:
        """Extract plain text from YouTube rich text objects."""
        if not obj:
            return None
        if isinstance(obj, str):
            return obj.strip() or None
        if isinstance(obj, dict):
            if "simpleText" in obj:
                text = obj["simpleText"].strip()
                return text if text else None
            if "runs" in obj:
                runs = obj["runs"]
                if isinstance(runs, list) and runs:
                    text = "".join(run.get("text", "") for run in runs).strip()
                    return text if text else None
        return None

    def _extract_channel_url(self, obj: Any) -> Optional[str]:
        """Extract channel URL from YouTube navigation endpoint."""
        try:
            if isinstance(obj, dict) and "runs" in obj:
                for run in obj["runs"]:
                    if "navigationEndpoint" in run:
                        browse_id = (
                            run["navigationEndpoint"].get("browseEndpoint", {}).get("browseId")
                        )
                        if browse_id:
                            return f"https://www.youtube.com/channel/{browse_id}"
        except (KeyError, TypeError) as exc:
            # Expected if the navigationEndpoint or browseId is missing or malformed.
            logger.debug(
                "Failed to extract channel URL from object: %r (exception: %r)",
                obj,
                exc,
            )
        return None

    def _extract_publish_date(self, obj: Any) -> Optional[str]:
        """Extract publish date (kept as original relative time string)."""
        return self._get_text(obj)

    def _extract_duration(self, obj: Any) -> Optional[str]:
        """Extract video duration from videoDetails."""
        try:
            if isinstance(obj, dict):
                return obj.get("durationSeconds") or obj.get("lengthSeconds")
        except (KeyError, TypeError):
            # Duration field may be missing or malformed; return None if not found.
            pass
        return None

    def _extract_view_count(self, obj: Any) -> Optional[int]:
        """Extract view count from YouTube number object."""
        try:
            if isinstance(obj, dict):
                text = self._get_text(obj.get("viewCountText"))
                if text:
                    # Parse "1.2M views" or "1,234,567 views"
                    match = re.search(r"([\d,.]+)", text)
                    if match:
                        count_str = match.group(1).replace(",", "")
                        if "M" in text:
                            return int(float(count_str) * 1_000_000)
                        elif "K" in text:
                            return int(float(count_str) * 1_000)
                        else:
                            return int(float(count_str))
        except (KeyError, ValueError, TypeError) as e:
            # Silently ignore parsing errors, but log for debugging and data quality monitoring.
            logger.debug(
                "Failed to extract view count from object: %r (error: %s)", obj, e
            )
        return None


_scraper: Optional[PlaylistScraper] = None


def get_playlist_scraper() -> PlaylistScraper:
    """Provide a singleton-ish PlaylistScraper instance."""
    global _scraper
    if _scraper is None:
        _scraper = PlaylistScraper()
    return _scraper
