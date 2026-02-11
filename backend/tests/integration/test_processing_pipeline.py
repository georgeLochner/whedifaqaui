"""Integration tests for the processing pipeline.

Test IDs covered:
  V2-I01  test_transcription_creates_transcript_record
  V2-I02  test_transcription_creates_segments
  V2-I03  test_audio_extraction
  V2-I04  test_transcription_with_test_video
  V2-I05  test_thumbnail_generated
  V3-I01  test_status_updates_during_processing
  C1-I01  test_chunking_creates_segments
  C1-I02  test_chunks_indexed_to_opensearch
  C1-I03  test_chunk_embeddings_generated
"""

import uuid
from datetime import date
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from sqlalchemy.orm import Session

from app.models.segment import Segment
from app.models.transcript import Transcript
from app.models.video import Video
from app.schemas.video import VideoStatus


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

MOCK_WHISPERX_RESULT = {
    "language": "en",
    "segments": [
        {"start": 0.0, "end": 5.0, "text": "Welcome to the sprint review meeting.", "speaker": "SPEAKER_00"},
        {"start": 5.0, "end": 10.0, "text": "Today we will discuss the architecture changes.", "speaker": "SPEAKER_01"},
        {"start": 10.0, "end": 15.0, "text": "The backend was migrated to FastAPI.", "speaker": "SPEAKER_00"},
    ],
}


def _fake_embeddings(texts):
    """Generate deterministic fake 768-dim embeddings."""
    result = []
    for text in texts:
        rng = np.random.RandomState(hash(text) % (2**31))
        vec = rng.randn(768).astype(np.float64)
        vec = vec / np.linalg.norm(vec)
        result.append(vec.tolist())
    return result


@pytest.fixture()
def video(db: Session) -> Video:
    """Create a test video in 'uploaded' status."""
    v = Video(
        id=uuid.uuid4(),
        title="Sprint Review",
        file_path="/data/videos/original/fake.mkv",
        recording_date=date(2024, 3, 1),
        participants=["Alice", "Bob"],
        status="uploaded",
    )
    db.add(v)
    db.flush()
    return v


@pytest.fixture()
def processing_video(db: Session) -> Video:
    """Create a test video in 'processing' status (ready for transcription)."""
    v = Video(
        id=uuid.uuid4(),
        title="Sprint Review",
        file_path="/data/videos/original/fake.mkv",
        recording_date=date(2024, 3, 1),
        participants=["Alice", "Bob"],
        status="processing",
    )
    db.add(v)
    db.flush()
    return v


@pytest.fixture()
def transcribing_video_with_segments(db: Session):
    """Create a video in 'transcribing' status with transcript and segments."""
    v = Video(
        id=uuid.uuid4(),
        title="Sprint Review",
        file_path="/data/videos/original/fake.mkv",
        recording_date=date(2024, 3, 1),
        status="transcribing",
    )
    db.add(v)
    db.flush()

    transcript = Transcript(
        video_id=v.id,
        full_text="Welcome. Architecture changes. FastAPI migration.",
        language="en",
        word_count=6,
    )
    db.add(transcript)
    db.flush()

    for i, (text, start, end, speaker) in enumerate([
        ("Welcome to the sprint review meeting.", 0.0, 5.0, "SPEAKER_00"),
        ("Today we will discuss the architecture changes.", 5.0, 10.0, "SPEAKER_01"),
        ("The backend was migrated to FastAPI.", 10.0, 15.0, "SPEAKER_00"),
    ]):
        seg = Segment(
            transcript_id=transcript.id,
            video_id=v.id,
            start_time=start,
            end_time=end,
            text=text,
            speaker=speaker,
            chunking_method="embedding",
        )
        db.add(seg)

    db.flush()
    return v, transcript


@pytest.fixture()
def chunking_video_with_segments(db: Session):
    """Create a video in 'chunking' status with segments ready for indexing."""
    v = Video(
        id=uuid.uuid4(),
        title="Sprint Review",
        file_path="/data/videos/original/fake.mkv",
        recording_date=date(2024, 3, 1),
        status="chunking",
    )
    db.add(v)
    db.flush()

    transcript = Transcript(
        video_id=v.id,
        full_text="Welcome. Architecture. FastAPI.",
        language="en",
        word_count=3,
    )
    db.add(transcript)
    db.flush()

    for text, start, end, speaker in [
        ("Welcome to the sprint review meeting.", 0.0, 5.0, "SPEAKER_00"),
        ("The backend was migrated to FastAPI.", 5.0, 10.0, "SPEAKER_01"),
    ]:
        seg = Segment(
            transcript_id=transcript.id,
            video_id=v.id,
            start_time=start,
            end_time=end,
            text=text,
            speaker=speaker,
            chunking_method="embedding",
        )
        db.add(seg)

    db.flush()
    return v, transcript


# ---------------------------------------------------------------------------
# V2-I01: Transcription creates transcript record
# ---------------------------------------------------------------------------


@patch("app.tasks.transcription.chunk_segments", create=True)
@patch("app.tasks.transcription.transcribe_audio")
@patch("app.tasks.transcription.Path")
def test_transcription_creates_transcript_record(
    mock_path_cls, mock_transcribe, mock_chain, db, processing_video
):
    """V2-I01: transcribe_video creates a Transcript row with correct video_id."""
    from app.tasks.transcription import transcribe_video

    mock_transcribe.return_value = MOCK_WHISPERX_RESULT
    mock_path_inst = MagicMock()
    mock_path_inst.exists.return_value = True
    mock_path_inst.unlink.return_value = None
    mock_path_cls.return_value = mock_path_inst
    mock_path_cls.__truediv__ = lambda self, other: mock_path_inst
    # Make Path() / "audio" / "{id}.wav" work
    mock_path_inst.__truediv__ = lambda self, other: mock_path_inst
    mock_path_inst.__str__ = lambda self: "/data/audio/fake.wav"
    mock_path_inst.mkdir = MagicMock()

    video_id = str(processing_video.id)

    with patch("app.tasks.transcription.SessionLocal", return_value=db), \
         patch.object(db, "close"):
        result = transcribe_video(video_id)

    assert result["video_id"] == video_id
    transcript = db.query(Transcript).filter(Transcript.video_id == processing_video.id).first()
    assert transcript is not None
    assert transcript.video_id == processing_video.id


# ---------------------------------------------------------------------------
# V2-I02: Transcription creates segments
# ---------------------------------------------------------------------------


@patch("app.tasks.transcription.chunk_segments", create=True)
@patch("app.tasks.transcription.transcribe_audio")
@patch("app.tasks.transcription.Path")
def test_transcription_creates_segments(
    mock_path_cls, mock_transcribe, mock_chain, db, processing_video
):
    """V2-I02: transcribe_video creates DB segments matching mock output count."""
    from app.tasks.transcription import transcribe_video

    mock_transcribe.return_value = MOCK_WHISPERX_RESULT
    mock_path_inst = MagicMock()
    mock_path_inst.exists.return_value = True
    mock_path_inst.unlink.return_value = None
    mock_path_cls.return_value = mock_path_inst
    mock_path_cls.__truediv__ = lambda self, other: mock_path_inst
    mock_path_inst.__truediv__ = lambda self, other: mock_path_inst
    mock_path_inst.__str__ = lambda self: "/data/audio/fake.wav"
    mock_path_inst.mkdir = MagicMock()

    video_id = str(processing_video.id)

    with patch("app.tasks.transcription.SessionLocal", return_value=db), \
         patch.object(db, "close"):
        result = transcribe_video(video_id)

    assert result["segment_count"] == 3
    segments = db.query(Segment).filter(Segment.video_id == processing_video.id).all()
    assert len(segments) == 3


# ---------------------------------------------------------------------------
# V2-I03: Audio extraction calls FFmpeg correctly
# ---------------------------------------------------------------------------


@patch("app.services.ffmpeg.subprocess.run")
@patch("app.services.ffmpeg.Path")
def test_audio_extraction(mock_path, mock_run):
    """V2-I03: extract_audio calls ffmpeg with correct WAV extraction args."""
    from app.services.ffmpeg import extract_audio

    mock_run.return_value = MagicMock(returncode=0)
    mock_path.return_value.parent.mkdir = MagicMock()

    result = extract_audio("/input/video.mp4", "/output/audio.wav")

    assert result is True
    call_args = mock_run.call_args[0][0]
    assert call_args[0] == "ffmpeg"
    assert "-vn" in call_args  # no video
    assert "pcm_s16le" in call_args  # 16-bit PCM
    assert "16000" in call_args  # 16kHz
    assert "/output/audio.wav" in call_args


# ---------------------------------------------------------------------------
# V2-I04: End-to-end transcription flow
# ---------------------------------------------------------------------------


@patch("app.tasks.transcription.chunk_segments", create=True)
@patch("app.tasks.transcription.transcribe_audio")
@patch("app.tasks.transcription.Path")
def test_transcription_with_test_video(
    mock_path_cls, mock_transcribe, mock_chain, db, processing_video
):
    """V2-I04: Full transcription flow creates transcript + segments."""
    from app.tasks.transcription import transcribe_video

    mock_transcribe.return_value = MOCK_WHISPERX_RESULT
    mock_path_inst = MagicMock()
    mock_path_inst.exists.return_value = True
    mock_path_inst.unlink.return_value = None
    mock_path_cls.return_value = mock_path_inst
    mock_path_cls.__truediv__ = lambda self, other: mock_path_inst
    mock_path_inst.__truediv__ = lambda self, other: mock_path_inst
    mock_path_inst.__str__ = lambda self: "/data/audio/fake.wav"
    mock_path_inst.mkdir = MagicMock()

    video_id = str(processing_video.id)

    with patch("app.tasks.transcription.SessionLocal", return_value=db), \
         patch.object(db, "close"):
        result = transcribe_video(video_id)

    # Transcript and segments both created
    transcript = db.query(Transcript).filter(Transcript.video_id == processing_video.id).first()
    assert transcript is not None
    assert transcript.word_count > 0

    segments = db.query(Segment).filter(Segment.video_id == processing_video.id).all()
    assert len(segments) == 3

    # Video status updated to transcribing
    video = db.get(Video, processing_video.id)
    assert video.status == VideoStatus.TRANSCRIBING.value


# ---------------------------------------------------------------------------
# V2-I05: Thumbnail generated during processing
# ---------------------------------------------------------------------------


@patch("app.tasks.video_processing.update_status")
@patch("app.tasks.video_processing.ffmpeg")
@patch("app.tasks.video_processing.SessionLocal")
def test_thumbnail_generated(mock_session_local, mock_ffmpeg, mock_update_status, db, video):
    """V2-I05: process_video sets thumbnail_path on video record."""
    from app.tasks.video_processing import process_video

    mock_video = MagicMock()
    mock_video.file_path = "/data/videos/original/test.mkv"
    mock_db = MagicMock()
    mock_db.get.return_value = mock_video
    mock_session_local.return_value = mock_db

    mock_ffmpeg.remux_to_mp4.return_value = True
    mock_ffmpeg.generate_thumbnail.return_value = True
    mock_ffmpeg.extract_audio.return_value = True
    mock_ffmpeg.get_duration.return_value = 120.0

    result = process_video(str(video.id))

    assert result["status"] == "processing_complete"
    assert mock_video.thumbnail_path is not None
    assert mock_video.thumbnail_path.endswith(".jpg")
    assert str(video.id) in mock_video.thumbnail_path


# ---------------------------------------------------------------------------
# V3-I01: Status updates through full pipeline
# ---------------------------------------------------------------------------


def test_status_updates_during_processing(db, video):
    """V3-I01: Status transitions: uploaded → processing → transcribing → chunking → indexing → ready."""
    from app.services.video import update_status

    vid = video.id

    # uploaded → processing
    update_status(db, vid, VideoStatus.PROCESSING)
    assert db.get(Video, vid).status == "processing"

    # processing → transcribing
    update_status(db, vid, VideoStatus.TRANSCRIBING)
    assert db.get(Video, vid).status == "transcribing"

    # transcribing → chunking
    update_status(db, vid, VideoStatus.CHUNKING)
    assert db.get(Video, vid).status == "chunking"

    # chunking → indexing
    update_status(db, vid, VideoStatus.INDEXING)
    assert db.get(Video, vid).status == "indexing"

    # indexing → ready
    update_status(db, vid, VideoStatus.READY)
    assert db.get(Video, vid).status == "ready"


# ---------------------------------------------------------------------------
# C1-I01: Chunking creates new segments
# ---------------------------------------------------------------------------


@patch("app.tasks.chunking.index_segments", create=True)
@patch("app.services.chunking.generate_embeddings", side_effect=_fake_embeddings)
def test_chunking_creates_segments(
    mock_embed, mock_chain, db, transcribing_video_with_segments
):
    """C1-I01: chunk_segments replaces segments with chunked versions."""
    from app.tasks.chunking import chunk_segments

    video, transcript = transcribing_video_with_segments
    video_id = str(video.id)

    original_count = db.query(Segment).filter(Segment.video_id == video.id).count()
    assert original_count == 3

    with patch("app.tasks.chunking.SessionLocal", return_value=db), \
         patch.object(db, "close"):
        result = chunk_segments(video_id)

    assert result["video_id"] == video_id
    new_segments = db.query(Segment).filter(Segment.video_id == video.id).all()
    assert len(new_segments) > 0
    # All new segments belong to the same transcript
    for seg in new_segments:
        assert seg.transcript_id == transcript.id
        assert seg.chunking_method == "embedding"


# ---------------------------------------------------------------------------
# C1-I02: Chunks indexed to OpenSearch
# ---------------------------------------------------------------------------


@patch("app.tasks.indexing.get_opensearch_client")
@patch("app.services.embedding.load_embedding_model")
def test_chunks_indexed_to_opensearch(
    mock_load_model, mock_get_client, db, chunking_video_with_segments
):
    """C1-I02: index_segments calls OpenSearch bulk() with correct document count."""
    from app.tasks.indexing import index_segments

    video, transcript = chunking_video_with_segments
    video_id = str(video.id)

    # Mock embedding model
    mock_model = MagicMock()
    def mock_encode(texts, **kwargs):
        result = []
        for t in texts:
            rng = np.random.RandomState(hash(t) % (2**31))
            vec = rng.randn(768).astype(np.float32)
            vec = vec / np.linalg.norm(vec)
            result.append(vec)
        return np.array(result)
    mock_model.encode = mock_encode
    mock_load_model.return_value = mock_model

    # Mock OpenSearch client
    mock_os_client = MagicMock()
    mock_os_client.indices.exists.return_value = True
    mock_os_client.bulk.return_value = {"errors": False, "items": []}
    mock_get_client.return_value = mock_os_client

    segment_count = db.query(Segment).filter(Segment.video_id == video.id).count()

    with patch("app.tasks.indexing.SessionLocal", return_value=db), \
         patch.object(db, "close"):
        result = index_segments(video_id)

    assert result["indexed_count"] == segment_count
    # bulk() called once with 2 items per segment (action + doc)
    mock_os_client.bulk.assert_called_once()
    bulk_body = mock_os_client.bulk.call_args[1].get("body") or mock_os_client.bulk.call_args[0][0]
    assert len(bulk_body) == segment_count * 2

    # Video status should be ready
    video = db.get(Video, video.id)
    assert video.status == "ready"


# ---------------------------------------------------------------------------
# C1-I03: Embeddings generated for chunks
# ---------------------------------------------------------------------------


@patch("app.tasks.indexing.get_opensearch_client")
@patch("app.services.embedding.load_embedding_model")
def test_chunk_embeddings_generated(
    mock_load_model, mock_get_client, db, chunking_video_with_segments
):
    """C1-I03: index_segments generates 768-dim embeddings for each segment."""
    from app.tasks.indexing import index_segments

    video, transcript = chunking_video_with_segments
    video_id = str(video.id)

    # Mock embedding model
    mock_model = MagicMock()
    encoded_embeddings = []

    def mock_encode(texts, **kwargs):
        result = []
        for t in texts:
            rng = np.random.RandomState(hash(t) % (2**31))
            vec = rng.randn(768).astype(np.float32)
            vec = vec / np.linalg.norm(vec)
            result.append(vec)
            encoded_embeddings.append(vec)
        return np.array(result)

    mock_model.encode = mock_encode
    mock_load_model.return_value = mock_model

    # Mock OpenSearch client
    mock_os_client = MagicMock()
    mock_os_client.indices.exists.return_value = True
    mock_os_client.bulk.return_value = {"errors": False, "items": []}
    mock_get_client.return_value = mock_os_client

    segment_count = db.query(Segment).filter(Segment.video_id == video.id).count()

    with patch("app.tasks.indexing.SessionLocal", return_value=db), \
         patch.object(db, "close"):
        result = index_segments(video_id)

    # Embeddings were generated for each segment
    assert len(encoded_embeddings) == segment_count
    for emb in encoded_embeddings:
        assert emb.shape == (768,)

    # Verify embeddings were sent to OpenSearch in bulk body
    bulk_body = mock_os_client.bulk.call_args[1].get("body") or mock_os_client.bulk.call_args[0][0]
    docs = [bulk_body[i] for i in range(1, len(bulk_body), 2)]
    for doc in docs:
        assert "embedding" in doc
        assert len(doc["embedding"]) == 768

    # All segments marked as indexed
    segments = db.query(Segment).filter(Segment.video_id == video.id).all()
    for seg in segments:
        assert seg.embedding_indexed is True
