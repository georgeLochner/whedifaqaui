"""Unit tests for Video schemas and status logic.

Test IDs covered:
  V1-U01  test_video_schema_validation
  V1-U02  test_video_file_extension_validation
  V1-U03  test_video_metadata_required_fields
  V1-U04  test_participants_array_parsing
  V3-U01  test_status_enum_values
  V3-U02  test_status_transition_validation
"""

from datetime import date
from io import BytesIO
from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from app.schemas.video import (
    VALID_TRANSITIONS,
    VideoCreate,
    VideoStatus,
)
from app.services.video import create_video, update_status


# ── V1-U01: VideoCreate schema accepts valid data, rejects invalid ────────


class TestVideoSchemaValidation:
    """V1-U01: VideoCreate schema validation."""

    def test_valid_data(self):
        schema = VideoCreate(
            title="Sprint Review",
            recording_date=date(2024, 3, 1),
        )
        assert schema.title == "Sprint Review"
        assert schema.recording_date == date(2024, 3, 1)

    def test_valid_with_optional_fields(self):
        schema = VideoCreate(
            title="Sprint Review",
            recording_date=date(2024, 3, 1),
            participants=["Alice", "Bob"],
            context_notes="Weekly sync",
        )
        assert schema.participants == ["Alice", "Bob"]
        assert schema.context_notes == "Weekly sync"

    def test_rejects_missing_title(self):
        with pytest.raises(ValidationError):
            VideoCreate(recording_date=date(2024, 3, 1))  # type: ignore[call-arg]

    def test_rejects_missing_date(self):
        with pytest.raises(ValidationError):
            VideoCreate(title="Sprint Review")  # type: ignore[call-arg]

    def test_title_max_length(self):
        with pytest.raises(ValidationError):
            VideoCreate(
                title="x" * 256,
                recording_date=date(2024, 3, 1),
            )


# ── V1-U02: Only .mkv files accepted ─────────────────────────────────────


class TestVideoFileExtensionValidation:
    """V1-U02: File extension validation in the service layer."""

    def _make_upload(self, filename: str) -> MagicMock:
        upload = MagicMock()
        upload.filename = filename
        upload.file = BytesIO(b"\x00" * 10)
        return upload

    def test_mkv_accepted(self, db, tmp_video_dir):
        video_data = VideoCreate(
            title="Test", recording_date=date(2024, 1, 1)
        )
        upload = self._make_upload("meeting.mkv")
        video = create_video(db, video_data, upload)
        assert video.id is not None

    def test_mp4_rejected(self, db, tmp_video_dir):
        video_data = VideoCreate(
            title="Test", recording_date=date(2024, 1, 1)
        )
        upload = self._make_upload("meeting.mp4")
        with pytest.raises(ValueError, match="Only .mkv files are accepted"):
            create_video(db, video_data, upload)

    def test_avi_rejected(self, db, tmp_video_dir):
        video_data = VideoCreate(
            title="Test", recording_date=date(2024, 1, 1)
        )
        upload = self._make_upload("meeting.avi")
        with pytest.raises(ValueError, match="Only .mkv files are accepted"):
            create_video(db, video_data, upload)

    def test_no_extension_rejected(self, db, tmp_video_dir):
        video_data = VideoCreate(
            title="Test", recording_date=date(2024, 1, 1)
        )
        upload = self._make_upload("meeting")
        with pytest.raises(ValueError, match="Only .mkv files are accepted"):
            create_video(db, video_data, upload)

    def test_mkv_case_insensitive(self, db, tmp_video_dir):
        video_data = VideoCreate(
            title="Test", recording_date=date(2024, 1, 1)
        )
        upload = self._make_upload("meeting.MKV")
        video = create_video(db, video_data, upload)
        assert video.id is not None


# ── V1-U03: Title and recording_date are required fields ─────────────────


class TestVideoMetadataRequiredFields:
    """V1-U03: Required field validation on VideoCreate."""

    def test_title_required(self):
        with pytest.raises(ValidationError) as exc_info:
            VideoCreate(recording_date=date(2024, 1, 1))  # type: ignore[call-arg]
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("title",) for e in errors)

    def test_recording_date_required(self):
        with pytest.raises(ValidationError) as exc_info:
            VideoCreate(title="My Video")  # type: ignore[call-arg]
        errors = exc_info.value.errors()
        assert any(e["loc"] == ("recording_date",) for e in errors)

    def test_participants_optional(self):
        schema = VideoCreate(
            title="Test", recording_date=date(2024, 1, 1)
        )
        assert schema.participants is None

    def test_context_notes_optional(self):
        schema = VideoCreate(
            title="Test", recording_date=date(2024, 1, 1)
        )
        assert schema.context_notes is None


# ── V1-U04: Participants array parsing ────────────────────────────────────


class TestParticipantsArrayParsing:
    """V1-U04: Participants list stored correctly."""

    def test_list_stored(self):
        schema = VideoCreate(
            title="Test",
            recording_date=date(2024, 1, 1),
            participants=["Alice", "Bob"],
        )
        assert schema.participants == ["Alice", "Bob"]

    def test_empty_list(self):
        schema = VideoCreate(
            title="Test",
            recording_date=date(2024, 1, 1),
            participants=[],
        )
        assert schema.participants == []

    def test_single_participant(self):
        schema = VideoCreate(
            title="Test",
            recording_date=date(2024, 1, 1),
            participants=["Solo"],
        )
        assert schema.participants == ["Solo"]

    def test_participants_persisted_to_db(self, db, tmp_video_dir):
        """Verify participants survive the round-trip through the service layer."""
        video_data = VideoCreate(
            title="Test",
            recording_date=date(2024, 1, 1),
            participants=["Alice", "Bob"],
        )
        upload = MagicMock()
        upload.filename = "test.mkv"
        upload.file = BytesIO(b"\x00" * 10)
        video = create_video(db, video_data, upload)
        assert video.participants == ["Alice", "Bob"]


# ── V3-U01: VideoStatus enum values ──────────────────────────────────────


class TestStatusEnumValues:
    """V3-U01: All expected status values defined."""

    def test_all_statuses_present(self):
        expected = {
            "uploaded",
            "processing",
            "transcribing",
            "chunking",
            "indexing",
            "ready",
            "error",
        }
        actual = {s.value for s in VideoStatus}
        assert actual == expected

    def test_status_count(self):
        assert len(VideoStatus) == 7


# ── V3-U02: Status transition validation ─────────────────────────────────


class TestStatusTransitionValidation:
    """V3-U02: VALID_TRANSITIONS allows legal moves, rejects illegal ones."""

    def test_uploaded_to_processing_allowed(self):
        assert VideoStatus.PROCESSING in VALID_TRANSITIONS[VideoStatus.UPLOADED]

    def test_uploaded_to_error_allowed(self):
        assert VideoStatus.ERROR in VALID_TRANSITIONS[VideoStatus.UPLOADED]

    def test_ready_to_uploaded_rejected(self):
        assert VideoStatus.UPLOADED not in VALID_TRANSITIONS[VideoStatus.READY]

    def test_error_has_no_transitions(self):
        assert VALID_TRANSITIONS[VideoStatus.ERROR] == []

    def test_full_happy_path(self):
        """Verify the entire happy-path chain is valid."""
        chain = [
            VideoStatus.UPLOADED,
            VideoStatus.PROCESSING,
            VideoStatus.TRANSCRIBING,
            VideoStatus.CHUNKING,
            VideoStatus.INDEXING,
            VideoStatus.READY,
        ]
        for current, next_status in zip(chain[:-1], chain[1:]):
            assert next_status in VALID_TRANSITIONS[current], (
                f"{current.value} -> {next_status.value} should be allowed"
            )

    def test_update_status_rejects_invalid_transition(self, db, make_video):
        """Verify update_status raises ValueError for an invalid transition."""
        video = make_video(status="ready")
        with pytest.raises(ValueError, match="Invalid status transition"):
            update_status(db, video.id, VideoStatus.UPLOADED)

    def test_update_status_accepts_valid_transition(self, db, make_video):
        """Verify update_status succeeds for a legal transition."""
        video = make_video(status="uploaded")
        updated = update_status(db, video.id, VideoStatus.PROCESSING)
        assert updated.status == "processing"
