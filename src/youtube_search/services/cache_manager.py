"""快取管理服務 - Redis 快取索引管理。"""

from __future__ import annotations

import json
import logging
from typing import Optional

from redis import Redis

from youtube_search.config import get_settings
from youtube_search.models.download import AudioFile

logger = logging.getLogger(__name__)


class CacheManagerService:
    """使用 Redis 管理已下載音檔的快取索引。"""

    def __init__(self, redis_client: Optional[Redis] = None):
        """
        初始化快取管理服務。

        Args:
            redis_client: Redis 客戶端實例（若為 None，將建立新連接）
        """
        self.config = get_settings()

        if redis_client:
            self.redis = redis_client
        else:
            self.redis = Redis(
                host=self.config.redis_host,
                port=self.config.redis_port,
                db=self.config.redis_db,
                password=self.config.redis_password,
                decode_responses=True,
            )

        # 快取鍵前綴
        self.cache_key_prefix = "download:audio:"
        logger.info("快取管理服務已初始化")

    def _get_cache_key(self, video_id: str) -> str:
        """生成快取鍵。"""
        return f"{self.cache_key_prefix}{video_id}"

    async def get_cached_audio(self, video_id: str) -> Optional[AudioFile]:
        """
        從快取取得已下載的音檔。

        Args:
            video_id: YouTube 影片 ID

        Returns:
            AudioFile: 音檔信息（若存在）；否則返回 None
        """
        try:
            cache_key = self._get_cache_key(video_id)
            cached_data = self.redis.get(cache_key)

            if not cached_data:
                logger.debug(f"快取未命中: {video_id}")
                return None

            # 反序列化音檔信息
            audio_dict = json.loads(cached_data)
            audio_file = AudioFile(**audio_dict)

            logger.info(f"快取命中: {video_id}")
            return audio_file

        except Exception as e:
            logger.warning(f"從快取獲取 {video_id} 時出錯: {str(e)}")
            return None

    async def set_cached_audio(self, audio_file: AudioFile) -> bool:
        """
        將已下載的音檔儲存到快取。

        Args:
            audio_file: 音檔信息

        Returns:
            bool: 是否成功儲存
        """
        try:
            cache_key = self._get_cache_key(audio_file.video_id)

            # 序列化音檔信息
            audio_dict = audio_file.model_dump(mode="json")
            cached_data = json.dumps(audio_dict)

            # TTL 計算
            ttl_seconds = self.config.cache_ttl_hours * 3600

            # 儲存到 Redis
            result = self.redis.setex(cache_key, ttl_seconds, cached_data)

            logger.info(
                f"音檔已快取: {audio_file.video_id}, TTL: {self.config.cache_ttl_hours}小時"
            )
            return result

        except Exception as e:
            logger.error(f"儲存快取 {audio_file.video_id} 時出錯: {str(e)}")
            return False

    async def is_cached(self, video_id: str) -> bool:
        """
        檢查影片是否已快取。

        Args:
            video_id: YouTube 影片 ID

        Returns:
            bool: 是否已快取
        """
        try:
            cache_key = self._get_cache_key(video_id)
            return self.redis.exists(cache_key) > 0
        except Exception as e:
            logger.warning(f"檢查快取狀態 {video_id} 時出錯: {str(e)}")
            return False

    async def get_cache_ttl(self, video_id: str) -> int:
        """
        獲取快取的剩餘 TTL。

        Args:
            video_id: YouTube 影片 ID

        Returns:
            int: 剩餘 TTL（秒）；若不存在返回 -2，若無過期時間返回 -1
        """
        try:
            cache_key = self._get_cache_key(video_id)
            ttl = self.redis.ttl(cache_key)
            logger.debug(f"快取 TTL {video_id}: {ttl} 秒")
            return ttl
        except Exception as e:
            logger.warning(f"獲取 TTL {video_id} 時出錯: {str(e)}")
            return -2

    async def delete_cache(self, video_id: str) -> bool:
        """
        刪除快取中的音檔記錄。

        Args:
            video_id: YouTube 影片 ID

        Returns:
            bool: 是否成功刪除
        """
        try:
            cache_key = self._get_cache_key(video_id)
            result = self.redis.delete(cache_key)
            logger.info(f"快取已刪除: {video_id}")
            return result > 0
        except Exception as e:
            logger.error(f"刪除快取 {video_id} 時出錯: {str(e)}")
            return False

    async def get_all_cached_video_ids(self) -> list[str]:
        """
        獲取所有已快取的影片 ID。

        Returns:
            list[str]: 影片 ID 清單
        """
        try:
            # 掃描所有符合前綴的鍵
            video_ids = []
            cursor = 0

            while True:
                cursor, keys = self.redis.scan(cursor, match=f"{self.cache_key_prefix}*")
                for key in keys:
                    video_id = key.replace(self.cache_key_prefix, "")
                    video_ids.append(video_id)

                if cursor == 0:
                    break

            logger.info(f"獲取所有快取影片: 共 {len(video_ids)} 個")
            return video_ids

        except Exception as e:
            logger.error(f"獲取所有快取影片 ID 時出錯: {str(e)}")
            return []

    async def cleanup_expired_cache(self) -> int:
        """
        清理已過期的快取（Redis 會自動清理，但此函數可主動檢查）。

        Returns:
            int: 清理的快取項數量
        """
        logger.info("開始清理過期快取...")
        cleaned_count = 0

        try:
            video_ids = await self.get_all_cached_video_ids()

            for video_id in video_ids:
                ttl = await self.get_cache_ttl(video_id)
                if ttl == -2:  # 鍵不存在
                    cleaned_count += 1

            logger.info(f"快取清理完成: 清理 {cleaned_count} 個項目")
            return cleaned_count

        except Exception as e:
            logger.error(f"清理過期快取時出錯: {str(e)}")
            return 0
