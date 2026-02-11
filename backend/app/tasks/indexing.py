import logging
import uuid
from datetime import datetime

from app.core.database import SessionLocal
from app.core.opensearch import (
    SEGMENTS_INDEX,
    ensure_segments_index,
    get_opensearch_client,
)
from app.models.segment import Segment
from app.schemas.video import VideoStatus
from app.services.embedding import generate_embeddings
from app.services.video import update_status
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.indexing.index_segments", bind=True, max_retries=2)
def index_segments(self, video_id: str) -> dict:
    """Generate embeddings and bulk index segments to OpenSearch."""
    from app.models.video import Video

    db = SessionLocal()
    try:
        vid = uuid.UUID(video_id)

        # Update status to INDEXING
        update_status(db, vid, VideoStatus.INDEXING)

        video = db.get(Video, vid)
        if video is None:
            raise ValueError(f"Video {video_id} not found")

        # Load all segments for this video
        segments = (
            db.query(Segment)
            .filter(Segment.video_id == vid)
            .order_by(Segment.start_time)
            .all()
        )
        if not segments:
            raise ValueError(f"No segments found for video {video_id}")

        # Generate embeddings for all segment texts
        texts = [seg.text for seg in segments]
        embeddings = generate_embeddings(texts)

        # Create OpenSearch client and ensure index exists
        client = get_opensearch_client()
        ensure_segments_index(client)

        # Bulk index documents
        bulk_body = []
        for seg, embedding in zip(segments, embeddings):
            doc = {
                "id": str(seg.id),
                "video_id": str(seg.video_id),
                "video_title": video.title,
                "transcript_id": str(seg.transcript_id),
                "text": seg.text,
                "embedding": embedding,
                "start_time": seg.start_time,
                "end_time": seg.end_time,
                "speaker": seg.speaker,
                "recording_date": video.recording_date.isoformat() if video.recording_date else None,
                "created_at": seg.created_at.isoformat() if seg.created_at else datetime.now().isoformat(),
            }
            bulk_body.append({"index": {"_index": SEGMENTS_INDEX, "_id": str(seg.id)}})
            bulk_body.append(doc)

        if bulk_body:
            response = client.bulk(body=bulk_body, refresh=True)
            if response.get("errors"):
                failed = [
                    item for item in response["items"]
                    if "error" in item.get("index", {})
                ]
                logger.error("Bulk indexing had %d errors", len(failed))
                raise RuntimeError(f"Bulk indexing failed for {len(failed)} documents")

        # Mark segments as indexed in DB
        for seg in segments:
            seg.embedding_indexed = True
        db.commit()

        # Update video status to READY
        update_status(db, vid, VideoStatus.READY)

        logger.info(
            "Indexed %d segments for video %s to OpenSearch",
            len(segments), video_id,
        )

        return {
            "video_id": video_id,
            "indexed_count": len(segments),
        }

    except Exception as exc:
        logger.error("Indexing failed for %s: %s", video_id, exc)
        try:
            update_status(db, uuid.UUID(video_id), VideoStatus.ERROR, error_message=str(exc))
        except Exception:
            logger.error("Failed to update error status for %s", video_id)
        raise
    finally:
        db.close()
