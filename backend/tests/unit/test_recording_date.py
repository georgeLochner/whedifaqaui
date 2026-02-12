"""V4 Recording Date unit tests.

Test IDs covered:
  V4-U01  test_recording_date_required
  V4-U02  test_recording_date_format
  V4-U03  test_date_stored_in_model
"""

from datetime import date

import pytest
from pydantic import ValidationError

from app.models.video import Video
from app.schemas.video import VideoCreate


def test_recording_date_required():
    """V4-U01: VideoCreate schema rejects missing recording_date."""
    with pytest.raises(ValidationError) as exc_info:
        VideoCreate(title="Test Video")  # type: ignore[call-arg]
    errors = exc_info.value.errors()
    assert any(e["loc"] == ("recording_date",) for e in errors)


def test_recording_date_format():
    """V4-U02: Date parsed correctly from ISO string."""
    schema = VideoCreate(
        title="Test Video",
        recording_date=date.fromisoformat("2023-01-05"),
    )
    assert schema.recording_date == date(2023, 1, 5)
    assert schema.recording_date.year == 2023
    assert schema.recording_date.month == 1
    assert schema.recording_date.day == 5


def test_date_stored_in_model(db, make_video):
    """V4-U03: Video model instance has accessible recording_date field."""
    video = make_video(recording_date=date(2023, 1, 5))
    assert isinstance(video, Video)
    assert video.recording_date == date(2023, 1, 5)
