"""V3-U01: Test VideoStatus enum values."""

from app.schemas.video import VideoStatus


def test_status_enum_values():
    """Verify VideoStatus enum has all 7 required status values."""
    expected = {"uploaded", "processing", "transcribing", "chunking", "indexing", "ready", "error"}
    actual = {s.value for s in VideoStatus}
    assert actual == expected


def test_status_enum_count():
    """Verify exactly 7 status values exist."""
    assert len(VideoStatus) == 7


def test_status_enum_is_string():
    """Verify VideoStatus members are string-compatible."""
    assert VideoStatus.UPLOADED == "uploaded"
    assert str(VideoStatus.READY) == "VideoStatus.READY"
    assert VideoStatus.READY.value == "ready"
