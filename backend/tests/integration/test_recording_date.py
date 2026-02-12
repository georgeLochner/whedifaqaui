"""V4 Recording Date integration tests.

Test IDs covered:
  V4-I03  test_date_index_exists
"""

from sqlalchemy import text


def test_date_index_exists(db):
    """V4-I03: Verify idx_videos_recording_date index exists in PostgreSQL."""
    result = db.execute(
        text(
            "SELECT indexname FROM pg_indexes "
            "WHERE tablename = 'videos' AND indexname = 'idx_videos_recording_date'"
        )
    )
    row = result.fetchone()
    assert row is not None, "idx_videos_recording_date index should exist"
    assert row[0] == "idx_videos_recording_date"
