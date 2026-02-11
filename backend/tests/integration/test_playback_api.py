"""Integration tests for the Playback API endpoints.

Test IDs covered:
  P1-I01  test_stream_endpoint_returns_video
  P1-I02  test_stream_supports_range_requests
  P1-I03  test_stream_content_type
  P3-I01  test_transcript_endpoint_returns_segments
  P3-I02  test_transcript_includes_speaker
"""

import uuid
from datetime import date

import pytest

from app.models.segment import Segment
from app.models.transcript import Transcript
from app.models.video import Video


@pytest.fixture()
def ready_video_with_file(db, tmp_path):
    """Create a video with status='ready' and a real MP4 file on disk."""
    # Create a small fake MP4 file
    mp4_path = tmp_path / "test_video.mp4"
    # ftyp box header (minimal valid-looking MP4 data)
    mp4_content = b"\x00\x00\x00\x1c" + b"ftypisom" + b"\x00" * 200
    mp4_path.write_bytes(mp4_content)

    video = Video(
        id=uuid.uuid4(),
        title="Ready Test Video",
        file_path="/data/videos/original/fake.mkv",
        processed_path=str(mp4_path),
        status="ready",
        recording_date=date(2024, 1, 15),
        duration=300,
    )
    db.add(video)
    db.flush()
    return video


@pytest.fixture()
def video_with_transcript(db, tmp_path):
    """Create a video with transcript and segments."""
    video = Video(
        id=uuid.uuid4(),
        title="Transcript Test Video",
        file_path="/data/videos/original/fake.mkv",
        status="ready",
        recording_date=date(2024, 2, 1),
        duration=120,
    )
    db.add(video)
    db.flush()

    transcript = Transcript(
        id=uuid.uuid4(),
        video_id=video.id,
        full_text="Hello world. Testing transcript.",
        language="en",
        word_count=5,
    )
    db.add(transcript)
    db.flush()

    segments_data = [
        {
            "start_time": 0.0,
            "end_time": 5.2,
            "text": "Hello world.",
            "speaker": "SPEAKER_00",
        },
        {
            "start_time": 5.2,
            "end_time": 10.8,
            "text": "Testing transcript.",
            "speaker": "SPEAKER_01",
        },
        {
            "start_time": 10.8,
            "end_time": 18.0,
            "text": "Third segment here.",
            "speaker": "SPEAKER_00",
        },
    ]
    for seg_data in segments_data:
        seg = Segment(
            id=uuid.uuid4(),
            transcript_id=transcript.id,
            video_id=video.id,
            **seg_data,
        )
        db.add(seg)
    db.flush()

    return video


# ── P1-I01: GET /videos/{id}/stream returns video bytes ──────────────────


class TestStreamEndpointReturnsVideo:
    """P1-I01"""

    def test_returns_video_bytes(self, client, ready_video_with_file):
        video = ready_video_with_file
        resp = client.get(f"/api/videos/{video.id}/stream")
        assert resp.status_code == 200
        assert len(resp.content) > 0

    def test_404_for_nonexistent_video(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"/api/videos/{fake_id}/stream")
        assert resp.status_code == 404

    def test_404_for_unprocessed_video(self, client, db):
        video = Video(
            id=uuid.uuid4(),
            title="Unprocessed",
            file_path="/data/videos/original/fake.mkv",
            status="uploaded",
            recording_date=date(2024, 1, 15),
        )
        db.add(video)
        db.flush()
        resp = client.get(f"/api/videos/{video.id}/stream")
        assert resp.status_code == 404


# ── P1-I02: Range header returns 206 Partial Content ────────────────────


class TestStreamSupportsRangeRequests:
    """P1-I02"""

    def test_range_request_returns_206(self, client, ready_video_with_file):
        video = ready_video_with_file
        resp = client.get(
            f"/api/videos/{video.id}/stream",
            headers={"Range": "bytes=0-49"},
        )
        assert resp.status_code == 206
        assert len(resp.content) == 50

    def test_content_range_header_present(self, client, ready_video_with_file):
        video = ready_video_with_file
        resp = client.get(
            f"/api/videos/{video.id}/stream",
            headers={"Range": "bytes=0-49"},
        )
        assert "content-range" in resp.headers
        assert resp.headers["content-range"].startswith("bytes 0-49/")

    def test_range_without_end(self, client, ready_video_with_file):
        video = ready_video_with_file
        resp = client.get(
            f"/api/videos/{video.id}/stream",
            headers={"Range": "bytes=10-"},
        )
        assert resp.status_code == 206
        assert len(resp.content) > 0


# ── P1-I03: Content-Type is video/mp4 ───────────────────────────────────


class TestStreamContentType:
    """P1-I03"""

    def test_content_type_is_mp4(self, client, ready_video_with_file):
        video = ready_video_with_file
        resp = client.get(f"/api/videos/{video.id}/stream")
        assert resp.headers["content-type"] == "video/mp4"

    def test_content_type_on_range_request(self, client, ready_video_with_file):
        video = ready_video_with_file
        resp = client.get(
            f"/api/videos/{video.id}/stream",
            headers={"Range": "bytes=0-49"},
        )
        assert resp.headers["content-type"] == "video/mp4"


# ── P3-I01: GET /videos/{id}/transcript returns segments ────────────────


class TestTranscriptEndpointReturnsSegments:
    """P3-I01"""

    def test_returns_segments_with_timestamps(self, client, video_with_transcript):
        video = video_with_transcript
        resp = client.get(f"/api/videos/{video.id}/transcript")
        assert resp.status_code == 200

        data = resp.json()
        assert data["video_id"] == str(video.id)
        assert data["count"] == 3
        assert len(data["segments"]) == 3

        # Verify ordering by start_time
        times = [seg["start_time"] for seg in data["segments"]]
        assert times == sorted(times)

    def test_segments_have_timestamp_formatted(self, client, video_with_transcript):
        video = video_with_transcript
        resp = client.get(f"/api/videos/{video.id}/transcript")
        data = resp.json()

        first_seg = data["segments"][0]
        assert "timestamp_formatted" in first_seg
        assert first_seg["timestamp_formatted"] == "0:00"

    def test_404_for_nonexistent_video(self, client):
        fake_id = uuid.uuid4()
        resp = client.get(f"/api/videos/{fake_id}/transcript")
        assert resp.status_code == 404

    def test_empty_segments_for_video_without_transcript(self, client, db):
        video = Video(
            id=uuid.uuid4(),
            title="No Transcript",
            file_path="/data/videos/original/fake.mkv",
            status="ready",
            recording_date=date(2024, 1, 15),
        )
        db.add(video)
        db.flush()

        resp = client.get(f"/api/videos/{video.id}/transcript")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 0
        assert data["segments"] == []


# ── P3-I02: Speaker field present in segment response ───────────────────


class TestTranscriptIncludesSpeaker:
    """P3-I02"""

    def test_speaker_field_present(self, client, video_with_transcript):
        video = video_with_transcript
        resp = client.get(f"/api/videos/{video.id}/transcript")
        data = resp.json()

        for seg in data["segments"]:
            assert "speaker" in seg

        assert data["segments"][0]["speaker"] == "SPEAKER_00"
        assert data["segments"][1]["speaker"] == "SPEAKER_01"

    def test_speaker_can_be_null(self, client, db):
        video = Video(
            id=uuid.uuid4(),
            title="Null Speaker Video",
            file_path="/data/videos/original/fake.mkv",
            status="ready",
            recording_date=date(2024, 1, 15),
        )
        db.add(video)
        db.flush()

        transcript = Transcript(
            id=uuid.uuid4(),
            video_id=video.id,
            full_text="Test text.",
            language="en",
            word_count=2,
        )
        db.add(transcript)
        db.flush()

        seg = Segment(
            id=uuid.uuid4(),
            transcript_id=transcript.id,
            video_id=video.id,
            start_time=0.0,
            end_time=5.0,
            text="Test text.",
            speaker=None,
        )
        db.add(seg)
        db.flush()

        resp = client.get(f"/api/videos/{video.id}/transcript")
        data = resp.json()
        assert data["segments"][0]["speaker"] is None
