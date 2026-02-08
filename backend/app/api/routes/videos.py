from uuid import UUID

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.video import (
    VideoListResponse,
    VideoResponse,
    VideoStatusResponse,
)
from app.services import video as video_service

router = APIRouter(prefix="/videos", tags=["videos"])


@router.post("", response_model=VideoResponse, status_code=201)
def upload_video(
    file: UploadFile = File(...),
    title: str = Form(...),
    recording_date: str = Form(...),
    participants: str = Form(""),
    context_notes: str = Form(""),
    db: Session = Depends(get_db),
):
    """Upload a video file with metadata."""
    from datetime import date as date_type

    from app.schemas.video import VideoCreate

    # Parse participants comma-separated string into list
    participants_list = (
        [p.strip() for p in participants.split(",") if p.strip()]
        if participants
        else None
    )

    try:
        parsed_date = date_type.fromisoformat(recording_date)
    except ValueError:
        raise HTTPException(status_code=422, detail="Invalid date format. Use YYYY-MM-DD.")

    video_data = VideoCreate(
        title=title,
        recording_date=parsed_date,
        participants=participants_list,
        context_notes=context_notes or None,
    )

    try:
        video = video_service.create_video(db, video_data, file)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Dispatch Celery processing task if available
    try:
        from app.tasks.video_processing import process_video

        process_video.delay(str(video.id))
    except (ImportError, Exception):
        pass  # Task not implemented yet

    return video


@router.get("", response_model=VideoListResponse)
def list_videos(
    skip: int = 0,
    limit: int = 20,
    db: Session = Depends(get_db),
):
    """List all videos with pagination."""
    videos, total = video_service.list_videos(db, skip=skip, limit=limit)
    return VideoListResponse(videos=videos, total=total)


@router.get("/{video_id}", response_model=VideoResponse)
def get_video(
    video_id: UUID,
    db: Session = Depends(get_db),
):
    """Get a single video by ID."""
    video = video_service.get_video(db, video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    return video


@router.get("/{video_id}/status", response_model=VideoStatusResponse)
def get_video_status(
    video_id: UUID,
    db: Session = Depends(get_db),
):
    """Get the processing status of a video (for polling)."""
    video = video_service.get_video(db, video_id)
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    return video
