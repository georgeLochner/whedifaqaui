import enum
from datetime import date, datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class VideoStatus(str, enum.Enum):
    """Status values for video processing pipeline."""

    UPLOADED = "uploaded"
    PROCESSING = "processing"
    TRANSCRIBING = "transcribing"
    CHUNKING = "chunking"
    INDEXING = "indexing"
    READY = "ready"
    ERROR = "error"


VALID_TRANSITIONS: dict[VideoStatus, list[VideoStatus]] = {
    VideoStatus.UPLOADED: [VideoStatus.PROCESSING, VideoStatus.ERROR],
    VideoStatus.PROCESSING: [VideoStatus.TRANSCRIBING, VideoStatus.ERROR],
    VideoStatus.TRANSCRIBING: [VideoStatus.CHUNKING, VideoStatus.ERROR],
    VideoStatus.CHUNKING: [VideoStatus.INDEXING, VideoStatus.ERROR],
    VideoStatus.INDEXING: [VideoStatus.READY, VideoStatus.ERROR],
    VideoStatus.READY: [VideoStatus.ERROR],
    VideoStatus.ERROR: [],
}


class VideoCreate(BaseModel):
    title: str = Field(..., max_length=255)
    recording_date: date
    participants: list[str] | None = None
    context_notes: str | None = None


class VideoResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    title: str
    file_path: str
    processed_path: str | None = None
    thumbnail_path: str | None = None
    duration: int | None = None
    recording_date: date
    participants: list[str] | None = None
    context_notes: str | None = None
    status: VideoStatus
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class VideoStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    status: VideoStatus
    error_message: str | None = None


class VideoListResponse(BaseModel):
    videos: list[VideoResponse]
    total: int
