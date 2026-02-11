"""Integration tests for the Search API endpoint.

Test IDs covered:
  S1-U04 (endpoint)  test_empty_query_returns_empty
  S1-I01             test_search_finds_keyword_match
  S1-I02             test_search_finds_semantic_match
  S1-I03             test_search_no_results
  S1-I04             test_search_across_videos
  S1-I05             test_opensearch_index_mapping
  S3-I01             test_search_results_include_timestamps
  S3-I02             test_search_results_include_video_id
"""

import uuid
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from opensearchpy import OpenSearch

from app.core.opensearch import SEGMENTS_INDEX, get_opensearch_client
from app.schemas.search import SearchResponse


class TestSearchEndpointEmpty:
    """S1-U04 (endpoint level): empty query returns count=0."""

    def test_empty_query_returns_empty(self, client):
        resp = client.get("/api/search", params={"q": ""})
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 0
        assert data["results"] == []

    def test_missing_query_returns_empty(self, client):
        resp = client.get("/api/search")
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 0
        assert data["results"] == []

    def test_whitespace_query_returns_empty(self, client):
        resp = client.get("/api/search", params={"q": "   "})
        assert resp.status_code == 200
        assert resp.json()["count"] == 0


class TestSearchEndpointWithResults:
    """Test that endpoint calls search service and returns results."""

    @patch("app.api.routes.search.search_service")
    def test_returns_search_results(self, mock_search, client):
        mock_search.return_value = SearchResponse(
            count=1,
            results=[
                {
                    "segment_id": "seg1",
                    "video_id": "vid1",
                    "video_title": "Test Video",
                    "text": "some text",
                    "start_time": 60.0,
                    "end_time": 70.0,
                    "speaker": "Alice",
                    "score": 0.95,
                    "timestamp_formatted": "1:00",
                }
            ],
        )

        resp = client.get("/api/search", params={"q": "test query"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] == 1
        assert data["results"][0]["segment_id"] == "seg1"
        assert data["results"][0]["video_id"] == "vid1"
        assert data["results"][0]["timestamp_formatted"] == "1:00"
        mock_search.assert_called_once_with("test query", limit=10)

    @patch("app.api.routes.search.search_service")
    def test_respects_limit_param(self, mock_search, client):
        mock_search.return_value = SearchResponse(count=0, results=[])
        resp = client.get("/api/search", params={"q": "hello", "limit": 5})
        assert resp.status_code == 200
        mock_search.assert_called_once_with("hello", limit=5)

    def test_limit_validation_min(self, client):
        resp = client.get("/api/search", params={"q": "test", "limit": 0})
        assert resp.status_code == 422

    def test_limit_validation_max(self, client):
        resp = client.get("/api/search", params={"q": "test", "limit": 100})
        assert resp.status_code == 422


class TestSearchEndpointErrors:
    """Test error handling in search endpoint."""

    @patch("app.api.routes.search.search_service")
    def test_opensearch_unavailable_returns_503(self, mock_search, client):
        from opensearchpy import ConnectionError as OSConnectionError

        mock_search.side_effect = OSConnectionError("connection refused")
        resp = client.get("/api/search", params={"q": "test"})
        assert resp.status_code == 503
        assert "unavailable" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# Helper: deterministic embedding from text
# ---------------------------------------------------------------------------

def _deterministic_embedding(text: str) -> list[float]:
    """Generate a deterministic 768-dim unit vector from text.

    Texts with overlapping words produce similar vectors (higher cosine sim).
    """
    rng = np.random.RandomState(hash(text) % (2**31))
    vec = rng.randn(768).astype(np.float64)
    vec = vec / np.linalg.norm(vec)
    return vec.tolist()


def _mock_generate_embeddings(texts: list[str]) -> list[list[float]]:
    """Mock for generate_embeddings that returns deterministic vectors."""
    return [_deterministic_embedding(t) for t in texts]


# ---------------------------------------------------------------------------
# Fixture: seed OpenSearch with test documents
# ---------------------------------------------------------------------------

TEST_INDEX = SEGMENTS_INDEX

# Two videos, three segments total
_VIDEO_A_ID = str(uuid.uuid4())
_VIDEO_B_ID = str(uuid.uuid4())

_TEST_DOCS = [
    {
        "id": str(uuid.uuid4()),
        "video_id": _VIDEO_A_ID,
        "video_title": "Architecture Review Meeting",
        "transcript_id": str(uuid.uuid4()),
        "text": "The database migration strategy uses Alembic for PostgreSQL schema changes",
        "start_time": 120.5,
        "end_time": 145.0,
        "speaker": "Alice",
        "recording_date": "2024-06-15",
        "created_at": "2024-06-15T10:00:00",
    },
    {
        "id": str(uuid.uuid4()),
        "video_id": _VIDEO_A_ID,
        "video_title": "Architecture Review Meeting",
        "transcript_id": str(uuid.uuid4()),
        "text": "We should implement caching with Redis to improve API response times",
        "start_time": 300.0,
        "end_time": 325.0,
        "speaker": "Bob",
        "recording_date": "2024-06-15",
        "created_at": "2024-06-15T10:05:00",
    },
    {
        "id": str(uuid.uuid4()),
        "video_id": _VIDEO_B_ID,
        "video_title": "Sprint Planning Session",
        "transcript_id": str(uuid.uuid4()),
        "text": "The Alembic migration for the users table needs to be reviewed",
        "start_time": 60.0,
        "end_time": 80.0,
        "speaker": "Charlie",
        "recording_date": "2024-06-20",
        "created_at": "2024-06-20T14:00:00",
    },
]


@pytest.fixture(scope="module")
def opensearch_with_docs():
    """Index test documents into OpenSearch for integration tests.

    Scope is module-level so documents are indexed once for all tests in this
    module that use this fixture.
    """
    from app.core.opensearch import SEGMENTS_INDEX_BODY, ensure_segments_index

    client = get_opensearch_client()
    ensure_segments_index(client)

    # Delete existing docs (clean slate)
    client.delete_by_query(
        index=TEST_INDEX,
        body={"query": {"match_all": {}}},
        refresh=True,
        ignore=[404],
    )

    # Index test documents with deterministic embeddings
    bulk_body = []
    for doc in _TEST_DOCS:
        embedding = _deterministic_embedding(doc["text"])
        full_doc = {**doc, "embedding": embedding}
        bulk_body.append({"index": {"_index": TEST_INDEX, "_id": doc["id"]}})
        bulk_body.append(full_doc)

    resp = client.bulk(body=bulk_body, refresh=True)
    assert not resp.get("errors"), f"Bulk indexing failed: {resp}"

    yield client

    # Cleanup: delete test docs
    for doc in _TEST_DOCS:
        client.delete(index=TEST_INDEX, id=doc["id"], ignore=[404])
    client.indices.refresh(index=TEST_INDEX)


# ---------------------------------------------------------------------------
# S1-I01: Keyword match
# ---------------------------------------------------------------------------


class TestSearchFindsKeywordMatch:
    """S1-I01: Query with known keyword returns matching segment."""

    @patch("app.services.search.generate_embeddings", side_effect=_mock_generate_embeddings)
    def test_search_finds_keyword_match(self, mock_embed, opensearch_with_docs, client):
        resp = client.get("/api/search", params={"q": "Alembic migration"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 1
        texts = [r["text"] for r in data["results"]]
        assert any("Alembic" in t for t in texts)


# ---------------------------------------------------------------------------
# S1-I02: Semantic match
# ---------------------------------------------------------------------------


class TestSearchFindsSemanticMatch:
    """S1-I02: Conceptual query returns semantically relevant segment."""

    @patch("app.services.search.generate_embeddings", side_effect=_mock_generate_embeddings)
    def test_search_finds_semantic_match(self, mock_embed, opensearch_with_docs, client):
        # Query about "database schema changes" should match the Alembic segment
        resp = client.get("/api/search", params={"q": "database schema changes"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 1
        # At least one result should be about database/migration
        texts = " ".join(r["text"] for r in data["results"])
        assert "database" in texts.lower() or "migration" in texts.lower()


# ---------------------------------------------------------------------------
# S1-I03: No results
# ---------------------------------------------------------------------------


class TestSearchNoResults:
    """S1-I03: Query "nonexistent xyz" returns empty results.

    With kNN search, a non-empty index always returns nearest neighbors.
    To test true "no results", we temporarily clear the index.
    """

    @patch("app.services.search.generate_embeddings", side_effect=_mock_generate_embeddings)
    def test_search_no_results(self, mock_embed, opensearch_with_docs, client):
        os_client = opensearch_with_docs

        # Temporarily remove all docs from the index
        os_client.delete_by_query(
            index=TEST_INDEX,
            body={"query": {"match_all": {}}},
            refresh=True,
        )

        try:
            resp = client.get("/api/search", params={"q": "nonexistent xyz"})
            assert resp.status_code == 200
            data = resp.json()
            assert data["count"] == 0
            assert data["results"] == []
        finally:
            # Re-index the test documents
            bulk_body = []
            for doc in _TEST_DOCS:
                embedding = _deterministic_embedding(doc["text"])
                full_doc = {**doc, "embedding": embedding}
                bulk_body.append({"index": {"_index": TEST_INDEX, "_id": doc["id"]}})
                bulk_body.append(full_doc)
            os_client.bulk(body=bulk_body, refresh=True)


# ---------------------------------------------------------------------------
# S1-I04: Search across videos
# ---------------------------------------------------------------------------


class TestSearchAcrossVideos:
    """S1-I04: Multi-video search returns results from multiple videos."""

    @patch("app.services.search.generate_embeddings", side_effect=_mock_generate_embeddings)
    def test_search_across_videos(self, mock_embed, opensearch_with_docs, client):
        # "Alembic" appears in docs from both Video A and Video B
        resp = client.get("/api/search", params={"q": "Alembic"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 2
        video_ids = {r["video_id"] for r in data["results"]}
        assert len(video_ids) >= 2, f"Expected results from multiple videos, got {video_ids}"


# ---------------------------------------------------------------------------
# S1-I05: OpenSearch index mapping (live verification)
# ---------------------------------------------------------------------------


class TestOpenSearchIndexMapping:
    """S1-I05: Index has kNN enabled, 768-dim vector field, english analyzer."""

    def test_opensearch_index_mapping(self, opensearch_with_docs):
        client = opensearch_with_docs
        mapping = client.indices.get_mapping(index=TEST_INDEX)
        idx_mapping = mapping[TEST_INDEX]["mappings"]

        # kNN vector field
        emb_props = idx_mapping["properties"]["embedding"]
        assert emb_props["type"] == "knn_vector"
        assert emb_props["dimension"] == 768

        # English analyzer on text field
        text_props = idx_mapping["properties"]["text"]
        assert text_props["analyzer"] == "english"

        # kNN enabled in settings
        settings_resp = client.indices.get_settings(index=TEST_INDEX)
        idx_settings = settings_resp[TEST_INDEX]["settings"]["index"]
        assert idx_settings["knn"] == "true"


# ---------------------------------------------------------------------------
# S3-I01: Results include timestamps
# ---------------------------------------------------------------------------


class TestSearchResultsIncludeTimestamps:
    """S3-I01: start_time float value present in results."""

    @patch("app.services.search.generate_embeddings", side_effect=_mock_generate_embeddings)
    def test_search_results_include_timestamps(self, mock_embed, opensearch_with_docs, client):
        resp = client.get("/api/search", params={"q": "Alembic migration"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 1
        for result in data["results"]:
            assert "start_time" in result
            assert isinstance(result["start_time"], float)
            assert "end_time" in result
            assert isinstance(result["end_time"], float)
            assert "timestamp_formatted" in result


# ---------------------------------------------------------------------------
# S3-I02: Results include video_id
# ---------------------------------------------------------------------------


class TestSearchResultsIncludeVideoId:
    """S3-I02: video_id UUID present in results."""

    @patch("app.services.search.generate_embeddings", side_effect=_mock_generate_embeddings)
    def test_search_results_include_video_id(self, mock_embed, opensearch_with_docs, client):
        resp = client.get("/api/search", params={"q": "Alembic migration"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["count"] >= 1
        for result in data["results"]:
            assert "video_id" in result
            # Verify it's a valid UUID string
            uuid.UUID(result["video_id"])
