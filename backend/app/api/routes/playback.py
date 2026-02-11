import os
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import Response
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.models.segment import Segment
from app.models.video import Video
from app.schemas.transcript import SegmentResponse, TranscriptResponse

router = APIRouter(prefix="/videos", tags=["playback"])


@router.get("/{video_id}/stream")
def stream_video(
    video_id: UUID,
    request: Request,
    db: Session = Depends(get_db),
):
    """Stream a processed video file with Range request support."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    if video.status != "ready":
        raise HTTPException(status_code=404, detail="Video not ready for playback")
    if not video.processed_path:
        raise HTTPException(status_code=404, detail="No processed video available")

    file_path = video.processed_path
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Video file not found on disk")

    file_size = os.path.getsize(file_path)
    range_header = request.headers.get("range")

    if range_header:
        # Parse Range header: "bytes=start-end"
        range_spec = range_header.strip().replace("bytes=", "")
        parts = range_spec.split("-")
        start = int(parts[0]) if parts[0] else 0
        end = int(parts[1]) if parts[1] else file_size - 1

        if start >= file_size:
            raise HTTPException(
                status_code=416,
                detail="Requested range not satisfiable",
            )

        end = min(end, file_size - 1)
        content_length = end - start + 1

        with open(file_path, "rb") as f:
            f.seek(start)
            data = f.read(content_length)

        return Response(
            content=data,
            status_code=206,
            media_type="video/mp4",
            headers={
                "Content-Range": f"bytes {start}-{end}/{file_size}",
                "Accept-Ranges": "bytes",
                "Content-Length": str(content_length),
            },
        )

    # No Range header — return full file
    with open(file_path, "rb") as f:
        data = f.read()

    return Response(
        content=data,
        status_code=200,
        media_type="video/mp4",
        headers={
            "Accept-Ranges": "bytes",
            "Content-Length": str(file_size),
        },
    )


@router.get("/{video_id}/thumbnail")
def get_thumbnail(
    video_id: UUID,
    db: Session = Depends(get_db),
):
    """Serve the thumbnail image for a video."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")
    if not video.thumbnail_path:
        raise HTTPException(status_code=404, detail="No thumbnail available")

    file_path = video.thumbnail_path
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Thumbnail file not found on disk")

    with open(file_path, "rb") as f:
        data = f.read()

    return Response(
        content=data,
        status_code=200,
        media_type="image/jpeg",
        headers={"Content-Length": str(len(data))},
    )


@router.get("/{video_id}/transcript", response_model=TranscriptResponse)
def get_transcript(
    video_id: UUID,
    db: Session = Depends(get_db),
):
    """Get transcript segments for a video, ordered by start_time."""
    video = db.query(Video).filter(Video.id == video_id).first()
    if video is None:
        raise HTTPException(status_code=404, detail="Video not found")

    segments = (
        db.query(Segment)
        .filter(Segment.video_id == video_id)
        .order_by(Segment.start_time)
        .all()
    )

    segment_responses = [
        SegmentResponse(
            id=str(seg.id),
            start_time=seg.start_time,
            end_time=seg.end_time,
            text=seg.text,
            speaker=seg.speaker,
        )
        for seg in segments
    ]

    return TranscriptResponse(
        video_id=str(video_id),
        segments=segment_responses,
        count=len(segment_responses),
    )
