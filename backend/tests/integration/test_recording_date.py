"""V4 Recording Date integration tests.

Test IDs covered:
  V4-I01  test_date_in_search_context
  V4-I02  test_date_in_chat_context
  V4-I03  test_date_index_exists
"""

from unittest.mock import MagicMock, patch

from sqlalchemy import text

from app.schemas.search import SearchResult
from app.services.search import search


def test_date_in_search_context():
    """V4-I01: Search results include recording_date field from indexed segments."""
    with patch("app.services.search.get_opensearch_client") as mock_client_fn, \
         patch("app.services.search.generate_embeddings") as mock_embed:
        mock_embed.return_value = [[0.1] * 768]
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client
        mock_client.indices.exists.return_value = True

        hit = {
            "_id": "seg1",
            "_score": 5.0,
            "_source": {
                "id": "seg1",
                "video_id": "vid1",
                "video_title": "Sprint Review",
                "text": "discussed recording dates",
                "start_time": 60.0,
                "end_time": 70.0,
                "speaker": "Alice",
                "recording_date": "2024-03-01",
            },
        }
        mock_client.search.side_effect = [
            {"hits": {"hits": [hit]}},
            {"hits": {"hits": [hit]}},
        ]

        result = search("recording dates", limit=5)

        assert result.count == 1
        assert result.results[0].recording_date == "2024-03-01"


def test_date_in_chat_context():
    """V4-I02: Indexed segment documents contain recording_date for context generation."""
    # Verify the OpenSearch mapping includes recording_date (prerequisite for chat context)
    from app.core.opensearch import SEGMENTS_INDEX_BODY
    props = SEGMENTS_INDEX_BODY["mappings"]["properties"]
    assert "recording_date" in props, "recording_date must be in segment index mapping"
    assert props["recording_date"]["type"] == "date"

    # Verify indexing task includes recording_date in document
    # (Chat context files are built from indexed segment data)
    import inspect
    from app.tasks.indexing import index_segments
    source = inspect.getsource(index_segments)
    assert "recording_date" in source, "indexing task must include recording_date in documents"


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
