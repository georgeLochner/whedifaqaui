"""Unit tests for search: index mapping and query construction (S1-I05, S1-U02, etc.)."""

from unittest.mock import MagicMock

from app.core.opensearch import (
    SEGMENTS_INDEX,
    SEGMENTS_INDEX_BODY,
    ensure_segments_index,
)


class TestSegmentsIndexMapping:
    """S1-I05 (partial): Verify segments_index mapping is correct."""

    def test_index_name(self):
        assert SEGMENTS_INDEX == "segments_index"

    def test_knn_enabled(self):
        """Index settings must enable knn."""
        assert SEGMENTS_INDEX_BODY["settings"]["index"]["knn"] is True

    def test_embedding_dimension_768(self):
        """Embedding field must be knn_vector with dimension 768."""
        emb = SEGMENTS_INDEX_BODY["mappings"]["properties"]["embedding"]
        assert emb["type"] == "knn_vector"
        assert emb["dimension"] == 768

    def test_embedding_hnsw_cosine(self):
        """Embedding uses HNSW with cosine similarity."""
        method = SEGMENTS_INDEX_BODY["mappings"]["properties"]["embedding"]["method"]
        assert method["name"] == "hnsw"
        assert method["space_type"] == "cosinesimil"

    def test_text_english_analyzer(self):
        """Text field uses English analyzer for BM25."""
        text_field = SEGMENTS_INDEX_BODY["mappings"]["properties"]["text"]
        assert text_field["type"] == "text"
        assert text_field["analyzer"] == "english"

    def test_required_fields_present(self):
        """All required fields are defined in the mapping."""
        props = SEGMENTS_INDEX_BODY["mappings"]["properties"]
        required = [
            "id", "video_id", "video_title", "transcript_id",
            "text", "embedding", "start_time", "end_time",
            "speaker", "recording_date", "created_at",
        ]
        for field in required:
            assert field in props, f"Missing field: {field}"


class TestEnsureSegmentsIndex:
    """Verify ensure_segments_index creates index when missing."""

    def test_creates_index_when_not_exists(self):
        client = MagicMock()
        client.indices.exists.return_value = False
        ensure_segments_index(client)
        client.indices.create.assert_called_once_with(
            index=SEGMENTS_INDEX, body=SEGMENTS_INDEX_BODY
        )

    def test_skips_when_index_exists(self):
        client = MagicMock()
        client.indices.exists.return_value = True
        ensure_segments_index(client)
        client.indices.create.assert_not_called()
