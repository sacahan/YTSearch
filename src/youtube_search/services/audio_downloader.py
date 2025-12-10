"""音檔下載服務 - yt-dlp 集成。"""

from __future__ import annotations

import asyncio
import json
import logging
import re
import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Optional

from youtube_search.config import get_settings
from youtube_search.models.download import AudioFile
from youtube_search.utils.errors import (
    DownloadFailedError,
    DurationExceededError,
    LiveStreamError,
    StorageFullError,
    VideoNotFoundError,
)

logger = logging.getLogger(__name__)


class AudioDownloaderService:
    """使用 yt-dlp 下載並轉換 YouTube 影片為 MP3 音檔的服務。"""

    def __init__(self):
        """初始化下載服務。"""
        self.config = get_settings()
        self.download_dir = Path(self.config.download_dir)
        self.download_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"下載目錄: {self.download_dir}")

    async def extract_video_info(self, video_id: str) -> dict:
        """
        獲取影片元數據（包含長度、標題、串流狀態等）。

        Args:
            video_id: YouTube 影片 ID

        Returns:
            dict: 包含影片信息的字典

        Raises:
            VideoNotFoundError: 影片不存在
            DurationExceededError: 影片長度超過限制
            LiveStreamError: 影片是直播
            DownloadFailedError: 其他下載失敗原因
        """
        try:
            # 使用 yt-dlp 獲取影片信息
            cmd = [
                "yt-dlp",
                "--dump-json",
                "--no-warnings",
                "--socket-timeout",
                "10",
                f"https://www.youtube.com/watch?v={video_id}",
            ]

            result = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                ),
                timeout=self.config.download_timeout,
            )

            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                stderr_str = stderr.decode("utf-8", errors="ignore")
                logger.warning(f"影片 {video_id} 獲取失敗: {stderr_str}")

                # 判斷錯誤類型
                if "unavailable" in stderr_str.lower() or "not found" in stderr_str.lower():
                    raise VideoNotFoundError(video_id=video_id)
                elif "live" in stderr_str.lower():
                    raise LiveStreamError(video_id=video_id)
                else:
                    raise DownloadFailedError(
                        video_id=video_id,
                        reason=stderr_str,
                    )

            # 解析 JSON 回應
            video_info = json.loads(stdout.decode("utf-8"))

            # 驗證影片長度
            duration = video_info.get("duration", 0)
            if duration > self.config.max_video_duration:
                raise DurationExceededError(
                    video_id=video_id,
                    video_duration=duration,
                    max_duration=self.config.max_video_duration,
                )

            # 檢查是否為直播
            if video_info.get("is_live", False):
                raise LiveStreamError(video_id=video_id)

            logger.info(
                f"影片信息獲取成功: {video_id}, 長度: {duration}秒, "
                f"標題: {video_info.get('title', 'Unknown')}"
            )

            return video_info

        except asyncio.TimeoutError:
            logger.error(f"影片 {video_id} 信息獲取逾時")
            raise DownloadFailedError(
                video_id=video_id,
                reason="獲取影片信息逾時",
            )
        except (VideoNotFoundError, DurationExceededError, LiveStreamError):
            raise
        except Exception as e:
            logger.error(f"影片 {video_id} 獲取失敗: {str(e)}")
            raise DownloadFailedError(
                video_id=video_id,
                reason=str(e),
            )

    async def download_and_convert(
        self, video_id: str, video_title: Optional[str] = None
    ) -> AudioFile:
        """
        下載影片並轉換為 128kbps MP3 音檔。

        Args:
            video_id: YouTube 影片 ID
            video_title: 影片標題（選擇性，用於檔案名稱）

        Returns:
            AudioFile: 下載完成的音檔信息

        Raises:
            DownloadFailedError: 下載或轉換失敗
            StorageFullError: 儲存空間不足
        """
        try:
            # 如果沒有提供標題，先獲取影片信息
            if not video_title:
                video_info = await self.extract_video_info(video_id)
                video_title = video_info.get("title", f"video_{video_id}")

            # 清理檔名
            clean_title = self._sanitize_filename(video_title)
            file_name = f"{video_id}_{clean_title}.mp3"
            file_path = self.download_dir / file_name

            # 檢查檔案是否已存在
            if file_path.exists():
                logger.info(f"音檔已存在: {file_path}")
                file_info = self._get_file_info(file_path, video_id, video_title)
                return file_info

            # 檢查磁盤空間（至少預留 100MB）
            self._check_storage_space(100 * 1024 * 1024)

            # 使用 yt-dlp 下載並轉換為 MP3
            output_template = str(self.download_dir / "%(id)s_%(title)s.mp3")
            cmd = [
                "yt-dlp",
                "-x",  # 提取音檔
                "--audio-format",
                "mp3",
                "--audio-quality",
                f"{self.config.audio_bitrate}K",
                "--no-warnings",
                "--socket-timeout",
                "10",
                "-o",
                output_template,
                f"https://www.youtube.com/watch?v={video_id}",
            ]

            logger.info(f"開始下載音檔: {video_id}")

            result = await asyncio.wait_for(
                asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                ),
                timeout=self.config.download_timeout,
            )

            stdout, stderr = await result.communicate()

            if result.returncode != 0:
                stderr_str = stderr.decode("utf-8", errors="ignore")
                logger.error(f"下載失敗 {video_id}: {stderr_str}")

                # 判斷錯誤類型
                if "copyright" in stderr_str.lower() or "blocked" in stderr_str.lower():
                    raise DownloadFailedError(
                        video_id=video_id,
                        reason="影片受版權或地區限制保護",
                    )
                elif "age" in stderr_str.lower():
                    raise DownloadFailedError(
                        video_id=video_id,
                        reason="影片需要年齡驗證",
                    )
                else:
                    raise DownloadFailedError(
                        video_id=video_id,
                        reason=stderr_str,
                    )

            # 查找實際下載的文件
            downloaded_file = self._find_downloaded_file(video_id)
            if not downloaded_file:
                raise DownloadFailedError(
                    video_id=video_id,
                    reason="下載完成但找不到音檔檔案",
                )

            logger.info(f"音檔下載成功: {downloaded_file}")

            # 獲取檔案信息
            file_info = self._get_file_info(downloaded_file, video_id, video_title)
            return file_info

        except asyncio.TimeoutError:
            logger.error(f"下載逾時: {video_id}")
            raise DownloadFailedError(
                video_id=video_id,
                reason="下載逾時（超過 5 分鐘）",
            )
        except (DownloadFailedError, StorageFullError, DurationExceededError):
            raise
        except Exception as e:
            logger.error(f"下載異常 {video_id}: {str(e)}")
            raise DownloadFailedError(
                video_id=video_id,
                reason=str(e),
            )

    def _sanitize_filename(self, filename: str) -> str:
        """清理檔名中的特殊字元。"""
        # 移除特殊字元，保留字母、數字、中文、連字符和底線
        filename = re.sub(r'[<>:"/\\|?*]', "", filename)
        filename = re.sub(r"\s+", "_", filename)
        # 限制長度
        max_length = 200
        return filename[:max_length]

    def _check_storage_space(self, required_bytes: int) -> None:
        """
        檢查磁盤空間是否充足。

        Args:
            required_bytes: 所需字節數

        Raises:
            StorageFullError: 空間不足
        """
        try:
            stat = shutil.disk_usage(self.download_dir)
            if stat.free < required_bytes:
                available_mb = stat.free / (1024 * 1024)
                required_mb = required_bytes / (1024 * 1024)
                raise StorageFullError(
                    reason=f"可用空間: {available_mb:.1f}MB, 所需: {required_mb:.1f}MB",
                )
        except StorageFullError:
            raise
        except Exception as e:
            logger.warning(f"檢查儲存空間時出錯: {str(e)}")

    def _find_downloaded_file(self, video_id: str) -> Optional[Path]:
        """在下載目錄中查找影片對應的 MP3 檔案。"""
        for file_path in self.download_dir.glob(f"{video_id}_*.mp3"):
            return file_path
        return None

    def _get_file_info(self, file_path: Path, video_id: str, title: str) -> AudioFile:
        """獲取檔案信息。"""
        stat = file_path.stat()
        return AudioFile(
            video_id=video_id,
            file_name=file_path.name,
            file_path=str(file_path),
            file_size=stat.st_size,
            duration=0,  # 暫時設為 0，可由快取管理器更新
            title=title,
        )

    async def batch_download(
        self,
        video_ids: list[str],
    ) -> dict[str, tuple[bool, Optional[AudioFile], Optional[str]]]:
        """
        並行下載多個影片。

        Args:
            video_ids: YouTube 影片 ID 清單

        Returns:
            dict: {video_id: (success, AudioFile|None, error_message|None)}
        """
        logger.info(f"開始批次下載: {len(video_ids)} 個影片")

        # 獲取所有影片的元數據
        info_tasks = [self.extract_video_info(vid) for vid in video_ids]
        info_results = await asyncio.gather(*info_tasks, return_exceptions=True)

        # 下載所有影片
        download_tasks = []
        for vid, info_result in zip(video_ids, info_results):
            if isinstance(info_result, Exception):
                download_tasks.append(None)
            else:
                title = info_result.get("title", f"video_{vid}")
                download_tasks.append(self.download_and_convert(vid, title))

        download_results = await asyncio.gather(*download_tasks, return_exceptions=True)

        # 整合結果
        result = {}
        for vid, download_result in zip(video_ids, download_results):
            if isinstance(download_result, Exception):
                error_msg = str(download_result)
                result[vid] = (False, None, error_msg)
                logger.warning(f"批次下載失敗: {vid} - {error_msg}")
            else:
                result[vid] = (True, download_result, None)
                logger.info(f"批次下載成功: {vid}")

        return result

    async def batch_download_as_zip(
        self,
        video_ids: list[str],
    ) -> tuple[Path, dict[str, tuple[bool, Optional[AudioFile], Optional[str]]]]:
        """
        並行下載多個影片並打包為 ZIP 檔案。

        Args:
            video_ids: YouTube 影片 ID 清單

        Returns:
            tuple: (zip_file_path, download_results)
                - zip_file_path: ZIP 檔案的完整路徑
                - download_results: {video_id: (success, AudioFile|None, error_message|None)}
        """
        logger.info(f"開始批次下載並打包: {len(video_ids)} 個影片")

        # 執行批次下載
        batch_results = await self.batch_download(video_ids)

        # 收集成功下載的檔案
        successful_files: list[Path] = []
        for vid, (success, audio_file, _error_msg) in batch_results.items():
            if success and audio_file:
                file_path = Path(audio_file.file_path)
                if file_path.exists():
                    successful_files.append(file_path)

        logger.info(f"成功下載 {len(successful_files)} 個檔案，開始打包")

        # 建立 ZIP 檔案
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        zip_filename = f"youtube_batch_download_{timestamp}.zip"
        zip_path = self.download_dir / zip_filename

        try:
            with zipfile.ZipFile(
                zip_path,
                "w",
                zipfile.ZIP_DEFLATED,
            ) as zip_file:
                for file_path in successful_files:
                    # 將檔案添加到 ZIP，使用原始檔名作為內部路徑
                    zip_file.write(file_path, arcname=file_path.name)
                    logger.debug(f"新增至 ZIP: {file_path.name}")

            # 驗證 ZIP 檔案
            if not zip_path.exists():
                raise DownloadFailedError(
                    message="ZIP 檔案建立失敗",
                    reason="檔案不存在",
                )

            zip_size = zip_path.stat().st_size
            logger.info(f"ZIP 檔案建立成功: {zip_path}, 大小: {zip_size} 字節")

            return zip_path, batch_results

        except Exception as e:
            logger.error(f"建立 ZIP 檔案失敗: {str(e)}")
            # 清理未完成的 ZIP 檔案
            if zip_path.exists():
                zip_path.unlink()
            raise DownloadFailedError(
                message="建立 ZIP 壓縮檔失敗",
                reason=str(e),
            )
