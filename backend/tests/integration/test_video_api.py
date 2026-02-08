"""Integration tests for the Video API endpoints.

Test IDs covered:
  V1-I01  test_upload_creates_video_record
  V1-I02  test_upload_stores_file
  V1-I03  test_upload_triggers_processing_task
  V1-I04  test_upload_returns_video_id
  V3-I02  test_status_endpoint_returns_current
  V3-I03  test_error_status_with_message
"""

import io
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from app.models.video import Video


def _upload(client: TestClient, *, filename: str = "meeting.mkv", title: str = "Sprint Review", recording_date: str = "2024-03-01", participants: str = "Alice,Bob", context_notes: str = "weekly sync"):
    """Helper: POST /api/videos with a small fake .mkv file."""
    file_content = b"\x1a\x45\xdf\xa3" + b"\x00" * 100
    return client.post(
        "/api/videos",
        data={
            "title": title,
            "recording_date": recording_date,
            "participants": participants,
            "context_notes": context_notes,
        },
        files={"file": (filename, io.BytesIO(file_content), "video/x-matroska")},
    )


# ── V1-I01: POST /videos creates DB record with status='uploaded' ────────


class TestUploadCreatesVideoRecord:
    """V1-I01"""

    def test_creates_record(self, client, db, tmp_video_dir):
        resp = _upload(client)
        assert resp.status_code == 201

        data = resp.json()
        video = db.get(Video, uuid.UUID(data["id"]))
        assert video is not None
        assert video.title == "Sprint Review"
        assert video.status == "uploaded"

    def test_record_has_correct_metadata(self, client, db, tmp_video_dir):
        resp = _upload(client)
        data = resp.json()
        assert data["recording_date"] == "2024-03-01"
        assert data["participants"] == ["Alice", "Bob"]
        assert data["context_notes"] == "weekly sync"


# ── V1-I02: File saved to /data/videos/original/{id}.mkv ────────────────


class TestUploadStoresFile:
    """V1-I02"""

    def test_file_written_to_disk(self, client, tmp_video_dir):
        resp = _upload(client)
        assert resp.status_code == 201

        video_id = resp.json()["id"]
        expected_path = tmp_video_dir / "original" / f"{video_id}.mkv"
        assert expected_path.exists()
        assert expected_path.stat().st_size > 0

    def test_file_path_stored_in_db(self, client, db, tmp_video_dir):
        resp = _upload(client)
        data = resp.json()
        video = db.get(Video, uuid.UUID(data["id"]))
        assert video.file_path.endswith(f"{data['id']}.mkv")


# ── V1-I03: Celery task queued after upload ──────────────────────────────


class TestUploadTriggersProcessingTask:
    """V1-I03"""

    def test_celery_task_dispatched(self, client, tmp_video_dir):
        mock_task = MagicMock()
        # Patch the module that the route handler lazily imports so we can
        # verify .delay() is called with the new video's ID.
        with patch.dict(
            "sys.modules",
            {"app.tasks.video_processing": MagicMock(process_video=mock_task)},
        ):
            resp = _upload(client)

        assert resp.status_code == 201
        mock_task.delay.assert_called_once_with(resp.json()["id"])


# ── V1-I04: Response includes valid UUID ─────────────────────────────────


class TestUploadReturnsVideoId:
    """V1-I04"""

    def test_response_contains_uuid(self, client, tmp_video_dir):
        resp = _upload(client)
        assert resp.status_code == 201
        data = resp.json()
        assert "id" in data
        # Verify it's a valid UUID
        parsed = uuid.UUID(data["id"])
        assert str(parsed) == data["id"]

    def test_status_is_uploaded(self, client, tmp_video_dir):
        resp = _upload(client)
        assert resp.json()["status"] == "uploaded"


# ── V3-I02: GET /videos/{id}/status returns current status ──────────────


class TestStatusEndpointReturnsCurrent:
    """V3-I02"""

    def test_returns_status(self, client, db, make_video, tmp_video_dir):
        video = make_video(status="processing")
        resp = client.get(f"/api/videos/{video.id}/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "processing"
        assert data["id"] == str(video.id)

    def test_404_for_nonexistent(self, client, tmp_video_dir):
        fake_id = uuid.uuid4()
        resp = client.get(f"/api/videos/{fake_id}/status")
        assert resp.status_code == 404


# ── V3-I03: Error status includes error_message ─────────────────────────


class TestErrorStatusWithMessage:
    """V3-I03"""

    def test_error_message_returned(self, client, db, make_video, tmp_video_dir):
        video = make_video(status="error", error_message="Transcription failed: corrupt file")
        resp = client.get(f"/api/videos/{video.id}/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "error"
        assert data["error_message"] == "Transcription failed: corrupt file"

    def test_no_error_message_when_not_error(self, client, db, make_video, tmp_video_dir):
        video = make_video(status="uploaded")
        resp = client.get(f"/api/videos/{video.id}/status")
        data = resp.json()
        assert data["error_message"] is None
