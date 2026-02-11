"""Unit tests for search: index mapping and query construction (S1-I05, S1-U02, etc.)."""

from unittest.mock import MagicMock, patch

from app.core.opensearch import (
    SEGMENTS_INDEX,
    SEGMENTS_INDEX_BODY,
    ensure_segments_index,
)
from app.schemas.search import SearchResponse, SearchResult
from app.services.search import (
    _apply_rrf,
    _format_timestamp,
    build_hybrid_query,
    search,
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


class TestBuildHybridQuery:
    """S1-U02: test_hybrid_query_construction."""

    def test_contains_bm25_match(self):
        """Query includes a BM25 match clause on the text field."""
        query = build_hybrid_query("test query", [0.1] * 768, limit=10)
        should = query["query"]["bool"]["should"]
        match_clauses = [c for c in should if "match" in c]
        assert len(match_clauses) >= 1
        assert match_clauses[0]["match"]["text"]["query"] == "test query"

    def test_contains_knn_clause(self):
        """Query includes a kNN clause on the embedding field."""
        embedding = [0.5] * 768
        query = build_hybrid_query("test", embedding, limit=5)
        assert "knn" in query
        assert query["knn"]["embedding"]["vector"] == embedding
        assert query["knn"]["embedding"]["k"] == 5

    def test_respects_limit(self):
        """Query size matches the requested limit."""
        query = build_hybrid_query("q", [0.0] * 768, limit=20)
        assert query["size"] == 20

    def test_both_bm25_and_knn_present(self):
        """Both BM25 and kNN search types are in the query."""
        query = build_hybrid_query("hello", [0.1] * 768)
        assert "query" in query and "bool" in query["query"]
        assert "knn" in query


class TestApplyRRF:
    """S1-U03: test_search_result_ranking - Results sorted by RRF score."""

    def _hit(self, doc_id: str, text: str = "text") -> dict:
        return {
            "_id": doc_id,
            "_source": {
                "id": doc_id,
                "video_id": "v1",
                "video_title": "Video",
                "text": text,
                "start_time": 10.0,
                "end_time": 20.0,
                "speaker": "Alice",
            },
        }

    def test_rrf_combines_scores(self):
        """Doc appearing in both lists gets higher score than single-list docs."""
        bm25 = [self._hit("a"), self._hit("b")]
        knn = [self._hit("a"), self._hit("c")]
        merged = _apply_rrf(bm25, knn, k=60)
        ids = [h["_id"] for h in merged]
        # 'a' appears in both lists → highest score
        assert ids[0] == "a"

    def test_rrf_sorted_descending(self):
        """Results are sorted by RRF score in descending order."""
        bm25 = [self._hit("x"), self._hit("y"), self._hit("z")]
        knn = [self._hit("z"), self._hit("x"), self._hit("y")]
        merged = _apply_rrf(bm25, knn, k=60)
        scores = [h["_rrf_score"] for h in merged]
        assert scores == sorted(scores, reverse=True)

    def test_rrf_empty_lists(self):
        """Empty input lists produce empty output."""
        assert _apply_rrf([], []) == []

    def test_rrf_single_list(self):
        """Works when one list is empty."""
        bm25 = [self._hit("a")]
        merged = _apply_rrf(bm25, [])
        assert len(merged) == 1
        assert merged[0]["_id"] == "a"


class TestFormatTimestamp:
    """Timestamp formatting helper."""

    def test_zero(self):
        assert _format_timestamp(0.0) == "0:00"

    def test_seconds_only(self):
        assert _format_timestamp(45.7) == "0:45"

    def test_minutes_and_seconds(self):
        assert _format_timestamp(754.0) == "12:34"

    def test_large_value(self):
        assert _format_timestamp(3661.0) == "61:01"


class TestSearchFunction:
    """S1-U04: test_empty_query_handled + search orchestration."""

    def test_empty_query_returns_empty(self):
        """Empty string returns SearchResponse with count=0."""
        result = search("")
        assert isinstance(result, SearchResponse)
        assert result.count == 0
        assert result.results == []

    def test_whitespace_query_returns_empty(self):
        """Whitespace-only query returns empty response."""
        result = search("   ")
        assert result.count == 0

    @patch("app.services.search.get_opensearch_client")
    @patch("app.services.search.generate_embeddings")
    def test_search_calls_opensearch(self, mock_embed, mock_client_fn):
        """search() generates embedding, queries OpenSearch, returns results."""
        mock_embed.return_value = [[0.1] * 768]

        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client
        mock_client.indices.exists.return_value = True

        # BM25 response
        bm25_hit = {
            "_id": "seg1",
            "_score": 5.0,
            "_source": {
                "id": "seg1",
                "video_id": "vid1",
                "video_title": "Test Video",
                "text": "some transcript text",
                "start_time": 60.0,
                "end_time": 70.0,
                "speaker": "Bob",
            },
        }
        # kNN response (same doc)
        knn_hit = {
            "_id": "seg1",
            "_score": 0.95,
            "_source": bm25_hit["_source"],
        }

        mock_client.search.side_effect = [
            {"hits": {"hits": [bm25_hit]}},
            {"hits": {"hits": [knn_hit]}},
        ]

        result = search("transcript text", limit=10)

        assert isinstance(result, SearchResponse)
        assert result.count == 1
        assert result.results[0].segment_id == "seg1"
        assert result.results[0].video_id == "vid1"
        assert result.results[0].timestamp_formatted == "1:00"
        assert result.results[0].speaker == "Bob"
        mock_embed.assert_called_once_with(["transcript text"])

    @patch("app.services.search.get_opensearch_client")
    @patch("app.services.search.generate_embeddings")
    def test_search_no_results(self, mock_embed, mock_client_fn):
        """search() with no matching docs returns count=0."""
        mock_embed.return_value = [[0.1] * 768]
        mock_client = MagicMock()
        mock_client_fn.return_value = mock_client
        mock_client.indices.exists.return_value = True
        mock_client.search.return_value = {"hits": {"hits": []}}

        result = search("nonexistent xyz", limit=10)
        assert result.count == 0
        assert result.results == []


class TestSearchResultSchema:
    """Verify SearchResult schema fields."""

    def test_search_result_fields(self):
        r = SearchResult(
            segment_id="s1",
            video_id="v1",
            video_title="Title",
            text="hello",
            start_time=10.0,
            end_time=20.0,
            speaker=None,
            score=0.5,
            timestamp_formatted="0:10",
        )
        assert r.segment_id == "s1"
        assert r.speaker is None
        assert r.score == 0.5

    def test_search_response_defaults(self):
        r = SearchResponse()
        assert r.count == 0
        assert r.results == []
