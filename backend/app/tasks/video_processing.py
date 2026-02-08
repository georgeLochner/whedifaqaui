import logging
import uuid
from datetime import datetime
from pathlib import Path

from app.core.config import settings
from app.core.database import SessionLocal
from app.schemas.video import VideoStatus
from app.services import ffmpeg
from app.services.video import update_status
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.video_processing.process_video", bind=True, max_retries=3)
def process_video(self, video_id: str) -> dict:
    """Process an uploaded video: remux to MP4, generate thumbnail, extract audio."""
    from app.models.video import Video

    db = SessionLocal()
    try:
        vid = uuid.UUID(video_id)

        # Update status to PROCESSING
        update_status(db, vid, VideoStatus.PROCESSING)

        video = db.get(Video, vid)
        if video is None:
            raise ValueError(f"Video {video_id} not found")

        # Set up output paths
        base = Path(settings.VIDEO_STORAGE_PATH)
        processed_dir = base / "processed"
        thumbnail_dir = base / "thumbnails"
        audio_dir = base / "audio"

        processed_path = str(processed_dir / f"{video_id}.mp4")
        thumbnail_path = str(thumbnail_dir / f"{video_id}.jpg")
        audio_path = str(audio_dir / f"{video_id}.wav")

        # Stage 1: Remux/transcode MKV → MP4
        ffmpeg.remux_to_mp4(video.file_path, processed_path)

        # Stage 2: Generate thumbnail from the MP4
        ffmpeg.generate_thumbnail(processed_path, thumbnail_path)

        # Stage 3: Extract audio as 16kHz mono WAV
        ffmpeg.extract_audio(processed_path, audio_path)

        # Get duration and update video record
        duration = ffmpeg.get_duration(processed_path)

        video.processed_path = processed_path
        video.thumbnail_path = thumbnail_path
        video.duration = int(duration)
        video.updated_at = datetime.now()
        db.commit()

        logger.info("Video %s processed successfully (duration=%ds)", video_id, int(duration))

        # Chain to transcription task
        try:
            from app.tasks.transcription import transcribe_video
            transcribe_video.delay(video_id)
        except (ImportError, Exception) as e:
            logger.warning("Could not chain to transcription task: %s", e)

        return {"video_id": video_id, "status": "processing_complete"}

    except Exception as exc:
        logger.error("Video processing failed for %s: %s", video_id, exc)
        try:
            update_status(db, uuid.UUID(video_id), VideoStatus.ERROR, error_message=str(exc))
        except Exception:
            logger.error("Failed to update error status for %s", video_id)
        raise
    finally:
        db.close()
