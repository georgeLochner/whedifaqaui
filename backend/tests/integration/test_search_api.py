"""Integration tests for the Search API endpoint.

Test IDs covered:
  S1-U04 (endpoint)  test_empty_query_returns_empty
  S1-I03             test_search_no_results
"""

from unittest.mock import MagicMock, patch

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
