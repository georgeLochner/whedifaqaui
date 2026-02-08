import json
import logging
import os
import uuid
from pathlib import Path

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.segment import Segment
from app.models.transcript import Transcript
from app.schemas.video import VideoStatus
from app.services.transcription import (
    calculate_word_count,
    parse_whisperx_output,
    transcribe_audio,
)
from app.services.video import update_status
from app.tasks.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="app.tasks.transcription.transcribe_video", bind=True, max_retries=2)
def transcribe_video(self, video_id: str) -> dict:
    """Transcribe a video's audio using WhisperX with speaker diarization."""
    from app.models.video import Video

    db = SessionLocal()
    try:
        vid = uuid.UUID(video_id)

        # Update status to TRANSCRIBING
        update_status(db, vid, VideoStatus.TRANSCRIBING)

        video = db.get(Video, vid)
        if video is None:
            raise ValueError(f"Video {video_id} not found")

        # Find audio file
        audio_path = str(Path(settings.VIDEO_STORAGE_PATH) / "audio" / f"{video_id}.wav")
        if not Path(audio_path).exists():
            raise FileNotFoundError(f"Audio file not found: {audio_path}")

        # Run WhisperX transcription
        device = os.environ.get("WHISPER_DEVICE", "cpu")
        hf_token = os.environ.get("HF_TOKEN")
        result = transcribe_audio(audio_path, device=device, hf_token=hf_token)

        # Parse output into normalized segments
        segments = parse_whisperx_output(result)
        if not segments:
            raise ValueError("Transcription produced no segments")

        # Save transcript JSON to /data/transcripts/{id}.json
        transcript_dir = Path(settings.TRANSCRIPT_STORAGE_PATH)
        transcript_dir.mkdir(parents=True, exist_ok=True)
        transcript_json_path = transcript_dir / f"{video_id}.json"
        with open(transcript_json_path, "w") as f:
            json.dump({"video_id": video_id, "segments": segments}, f, indent=2)
        logger.info("Saved transcript JSON to %s", transcript_json_path)

        # Build full text from segments
        full_text = " ".join(seg["text"] for seg in segments)
        word_count = calculate_word_count(segments)

        # Create Transcript DB record
        transcript = Transcript(
            video_id=vid,
            full_text=full_text,
            language=result.get("language", "en"),
            word_count=word_count,
        )
        db.add(transcript)
        db.flush()  # get transcript.id

        # Create Segment DB records
        for seg in segments:
            db_segment = Segment(
                transcript_id=transcript.id,
                video_id=vid,
                start_time=seg["start"],
                end_time=seg["end"],
                text=seg["text"],
                speaker=seg["speaker"],
                chunking_method="embedding",
            )
            db.add(db_segment)

        db.commit()
        logger.info(
            "Created transcript (id=%s) with %d segments for video %s",
            transcript.id, len(segments), video_id,
        )

        # Clean up audio WAV file
        try:
            Path(audio_path).unlink()
            logger.info("Cleaned up audio file: %s", audio_path)
        except OSError as e:
            logger.warning("Failed to clean up audio file %s: %s", audio_path, e)

        # Chain to chunking task
        try:
            from app.tasks.chunking import chunk_segments
            chunk_segments.delay(video_id)
        except (ImportError, Exception) as e:
            logger.warning("Could not chain to chunking task: %s", e)

        return {
            "video_id": video_id,
            "transcript_id": str(transcript.id),
            "segment_count": len(segments),
            "word_count": word_count,
        }

    except Exception as exc:
        logger.error("Transcription failed for %s: %s", video_id, exc)
        try:
            update_status(db, uuid.UUID(video_id), VideoStatus.ERROR, error_message=str(exc))
        except Exception:
            logger.error("Failed to update error status for %s", video_id)
        raise
    finally:
        db.close()
