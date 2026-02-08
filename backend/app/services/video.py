import shutil
import uuid
from datetime import datetime
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.video import Video
from app.schemas.video import VALID_TRANSITIONS, VideoCreate, VideoStatus


def create_video(db: Session, video_data: VideoCreate, file: UploadFile) -> Video:
    """Create a video record and save the uploaded file."""
    filename = file.filename or ""
    if not filename.lower().endswith(".mkv"):
        raise ValueError("Only .mkv files are accepted")

    video = Video(
        title=video_data.title,
        recording_date=video_data.recording_date,
        participants=video_data.participants,
        context_notes=video_data.context_notes,
        file_path="",  # placeholder, updated after we know the ID
        status=VideoStatus.UPLOADED.value,
    )
    db.add(video)
    db.flush()  # get the generated ID

    # Save file to /data/videos/original/{id}.mkv
    original_dir = Path(settings.VIDEO_STORAGE_PATH) / "original"
    original_dir.mkdir(parents=True, exist_ok=True)
    file_path = original_dir / f"{video.id}.mkv"

    with open(file_path, "wb") as dest:
        shutil.copyfileobj(file.file, dest)

    video.file_path = str(file_path)
    db.commit()
    db.refresh(video)
    return video


def get_video(db: Session, video_id: uuid.UUID) -> Video | None:
    """Get a video by ID."""
    return db.get(Video, video_id)


def list_videos(
    db: Session, skip: int = 0, limit: int = 20
) -> tuple[list[Video], int]:
    """List videos with pagination, ordered by created_at descending."""
    total = db.scalar(select(func.count()).select_from(Video))
    videos = (
        db.execute(
            select(Video).order_by(Video.created_at.desc()).offset(skip).limit(limit)
        )
        .scalars()
        .all()
    )
    return list(videos), total or 0


def update_status(
    db: Session,
    video_id: uuid.UUID,
    new_status: VideoStatus,
    error_message: str | None = None,
) -> Video:
    """Update video status, validating the transition."""
    video = db.get(Video, video_id)
    if video is None:
        raise ValueError(f"Video {video_id} not found")

    current_status = VideoStatus(video.status)
    allowed = VALID_TRANSITIONS.get(current_status, [])
    if new_status not in allowed:
        raise ValueError(
            f"Invalid status transition: {current_status.value} -> {new_status.value}"
        )

    video.status = new_status.value
    if error_message is not None:
        video.error_message = error_message
    video.updated_at = datetime.now()
    db.commit()
    db.refresh(video)
    return video
