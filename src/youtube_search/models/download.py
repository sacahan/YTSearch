"""下載功能的資料模型定義。"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, Field


class DownloadStatus(str, Enum):
    """下載狀態列舉。"""

    PENDING = "pending"
    DOWNLOADING = "downloading"
    SUCCESS = "success"
    FAILED = "failed"
    CANCELLED = "cancelled"


class DownloadFormat(str, Enum):
    """下載格式列舉。"""

    LINK = "link"  # 返回下載連結
    STREAM = "stream"  # 直接串流 MP3


class DownloadErrorType(str, Enum):
    """下載錯誤類型列舉。"""

    VIDEO_NOT_FOUND = "video_not_found"
    DURATION_EXCEEDED = "duration_exceeded"
    LIVE_STREAM = "live_stream"
    DOWNLOAD_FAILED = "download_failed"
    STORAGE_FULL = "storage_full"
    TIMEOUT = "timeout"
    INVALID_VIDEO_ID = "invalid_video_id"
    UNKNOWN = "unknown"


class AudioFile(BaseModel):
    """音檔模型。"""

    video_id: str = Field(..., description="YouTube 影片 ID")
    file_name: str = Field(..., description="本地檔案名稱（無路徑）")
    file_path: str = Field(..., description="完整檔案路徑")
    file_size: int = Field(..., ge=0, description="檔案大小（字節）")
    duration: int = Field(..., ge=0, description="音檔長度（秒）")
    title: str = Field(..., description="影片標題")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="建立時間")


class DownloadLog(BaseModel):
    """下載日誌模型。"""

    video_id: str = Field(..., description="YouTube 影片 ID")
    status: DownloadStatus = Field(..., description="下載狀態")
    error_type: Optional[DownloadErrorType] = Field(
        default=None,
        description="錯誤類型（失敗時）",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="錯誤訊息（失敗時）",
    )
    ip_address: Optional[str] = Field(default=None, description="請求者 IP 位址")
    timestamp: datetime = Field(default_factory=datetime.utcnow, description="時間戳記")
    duration: Optional[int] = Field(default=None, description="處理耗時（毫秒）")


class DownloadRequest(BaseModel):
    """下載請求基類。"""

    video_id: str = Field(..., min_length=10, max_length=20, description="YouTube 影片 ID")
    format: DownloadFormat = Field(
        default=DownloadFormat.LINK,
        description="返回格式 (link 或 stream)",
    )


class DownloadAudioRequest(DownloadRequest):
    """單一音檔下載 API 請求。"""

    pass


class DownloadAudioResponse(BaseModel):
    """單一音檔下載 API 回應。"""

    video_id: str = Field(..., description="YouTube 影片 ID")
    title: str = Field(..., description="影片標題")
    duration: int = Field(..., ge=0, description="音檔長度（秒）")
    download_url: Optional[str] = Field(
        default=None,
        description="下載連結（format=link 時返回）",
    )
    cached: bool = Field(
        default=False,
        description="是否從快取直接返回",
    )
    file_size: Optional[int] = Field(
        default=None,
        description="音檔大小（字節）",
    )


class BatchDownloadItem(BaseModel):
    """批次下載項目。"""

    video_id: str = Field(..., description="YouTube 影片 ID")
    status: str = Field(..., description="下載狀態 (success, failed)")
    download_url: Optional[str] = Field(
        default=None,
        description="下載連結（成功時）",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="錯誤訊息（失敗時）",
    )
    duration: Optional[int] = Field(
        default=None,
        description="音檔長度（秒，成功時）",
    )
    cached: bool = Field(
        default=False,
        description="是否從快取直接返回",
    )


class BatchDownloadRequest(BaseModel):
    """批次下載 API 請求。"""

    video_ids: list[str] = Field(
        ...,
        min_items=1,
        max_items=20,
        description="YouTube 影片 ID 清單（最多 20 個）",
    )


class BatchDownloadResponse(BaseModel):
    """批次下載 API 回應。"""

    total: int = Field(..., ge=0, description="請求總數")
    successful: int = Field(..., ge=0, description="成功數量")
    failed: int = Field(..., ge=0, description="失敗數量")
    items: list[BatchDownloadItem] = Field(
        ...,
        description="各影片下載結果",
    )
