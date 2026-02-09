import logging
import uuid

from app.core.database import SessionLocal
from app.models.segment import Segment
from app.schemas.video import VideoStatus
from app.services.chunking import semantic_chunk
from app.services.video import update_status
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.chunking.chunk_segments", bind=True, max_retries=2)
def chunk_segments(self, video_id: str) -> dict:
    """Run semantic chunking on transcript segments, replacing them with final chunks."""
    from app.models.transcript import Transcript

    db = SessionLocal()
    try:
        vid = uuid.UUID(video_id)

        # Update status to CHUNKING
        update_status(db, vid, VideoStatus.CHUNKING)

        # Load existing segments for this video
        segments = (
            db.query(Segment)
            .filter(Segment.video_id == vid)
            .order_by(Segment.start_time)
            .all()
        )
        if not segments:
            raise ValueError(f"No segments found for video {video_id}")

        # Get transcript_id from existing segments
        transcript_id = segments[0].transcript_id

        # Convert DB segments to list of dicts for chunking service
        segment_dicts = [
            {
                "text": seg.text,
                "start_time": seg.start_time,
                "end_time": seg.end_time,
                "speaker": seg.speaker or "SPEAKER_00",
            }
            for seg in segments
        ]

        # Run semantic chunking
        chunks = semantic_chunk(
            segment_dicts,
            similarity_threshold=0.5,
            min_chunk_tokens=100,
            max_chunk_tokens=500,
        )

        if not chunks:
            raise ValueError(f"Chunking produced no chunks for video {video_id}")

        # Delete initial transcription segments
        db.query(Segment).filter(Segment.video_id == vid).delete()

        # Create new Segment records from chunked output
        for chunk in chunks:
            db_segment = Segment(
                transcript_id=transcript_id,
                video_id=vid,
                start_time=chunk["start_time"],
                end_time=chunk["end_time"],
                text=chunk["text"],
                speaker=chunk.get("speaker", "SPEAKER_00"),
                chunking_method="embedding",
            )
            db.add(db_segment)

        db.commit()
        logger.info(
            "Chunking complete: %d segments → %d chunks for video %s",
            len(segment_dicts), len(chunks), video_id,
        )

        # Chain to indexing task
        try:
            from app.tasks.indexing import index_segments
            index_segments.delay(video_id)
        except (ImportError, Exception) as e:
            logger.warning("Could not chain to indexing task: %s", e)

        return {
            "video_id": video_id,
            "original_segments": len(segment_dicts),
            "chunks": len(chunks),
        }

    except Exception as exc:
        logger.error("Chunking failed for %s: %s", video_id, exc)
        try:
            update_status(db, uuid.UUID(video_id), VideoStatus.ERROR, error_message=str(exc))
        except Exception:
            logger.error("Failed to update error status for %s", video_id)
        raise
    finally:
        db.close()
