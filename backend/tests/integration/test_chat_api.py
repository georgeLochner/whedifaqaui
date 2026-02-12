"""Integration tests for the Chat API endpoint.

Test IDs covered:
  S7-I01  test_chat_endpoint_new_conversation
  S7-I02  test_chat_endpoint_resume_conversation
  S7-I03  test_chat_searches_opensearch
  S7-I04  test_chat_context_preparation
  S7-I05  test_chat_response_includes_citations
  S7-I06  test_chat_empty_search_results
  S7-I07  test_chat_claude_error
  S2-I01  test_summary_cites_multiple_sources
  S2-I02  test_summary_synthesizes_content
"""

from unittest.mock import MagicMock, patch

import pytest

from app.schemas.search import SearchResponse, SearchResult
from app.services.claude import ClaudeError, ClaudeResponse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_search_result(**overrides) -> SearchResult:
    defaults = {
        "segment_id": "seg-1",
        "video_id": "vid-1",
        "video_title": "Auth Meeting",
        "text": "We decided to migrate from Auth0 to Cognito.",
        "start_time": 125.5,
        "end_time": 140.0,
        "speaker": "SPEAKER_00",
        "recording_date": "2023-01-05",
        "score": 0.85,
        "timestamp_formatted": "2:05",
    }
    defaults.update(overrides)
    return SearchResult(**defaults)


def _make_claude_response(text: str, conv_id: str = "conv-new-123") -> ClaudeResponse:
    return ClaudeResponse(result=text, conversation_id=conv_id)


SINGLE_RESULT = SearchResponse(
    count=1,
    results=[_make_search_result()],
)

MULTI_RESULTS = SearchResponse(
    count=2,
    results=[
        _make_search_result(
            video_id="vid-1",
            video_title="Auth Meeting",
            segment_id="seg-1",
            text="We decided to migrate from Auth0 to Cognito.",
            start_time=125.5,
        ),
        _make_search_result(
            video_id="vid-2",
            video_title="Deploy Review",
            segment_id="seg-2",
            text="The deployment uses a blue-green strategy.",
            start_time=300.0,
        ),
    ],
)

EMPTY_RESULTS = SearchResponse(count=0, results=[])


# ---------------------------------------------------------------------------
# S7-I01: New conversation
# ---------------------------------------------------------------------------

class TestChatNewConversation:
    """S7-I01: POST /api/chat without conversation_id returns message + new id."""

    @patch("app.services.chat.claude")
    @patch("app.services.chat.search")
    def test_chat_endpoint_new_conversation(self, mock_search, mock_claude, client, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.chat.TEMP_DIR", tmp_path)
        mock_search.return_value = SINGLE_RESULT
        mock_claude.query.return_value = _make_claude_response(
            "The team uses Cognito [Auth Meeting @ 2:05]."
        )

        resp = client.post("/api/chat", json={"message": "What auth system?"})

        assert resp.status_code == 200
        data = resp.json()
        assert "message" in data
        assert data["conversation_id"] == "conv-new-123"
        assert "Cognito" in data["message"]


# ---------------------------------------------------------------------------
# S7-I02: Resume conversation
# ---------------------------------------------------------------------------

class TestChatResumeConversation:
    """S7-I02: POST /api/chat with conversation_id passes it through."""

    @patch("app.services.chat.claude")
    @patch("app.services.chat.search")
    def test_chat_endpoint_resume_conversation(self, mock_search, mock_claude, client, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.chat.TEMP_DIR", tmp_path)
        mock_search.return_value = SINGLE_RESULT
        mock_claude.query.return_value = _make_claude_response(
            "More details about Cognito.", conv_id="existing-conv-456"
        )

        resp = client.post("/api/chat", json={
            "message": "Tell me more",
            "conversation_id": "existing-conv-456",
        })

        assert resp.status_code == 200
        data = resp.json()
        assert data["conversation_id"] == "existing-conv-456"
        mock_claude.query.assert_called_once()
        _, kwargs = mock_claude.query.call_args
        assert kwargs["conversation_id"] == "existing-conv-456"


# ---------------------------------------------------------------------------
# S7-I03: Chat triggers search
# ---------------------------------------------------------------------------

class TestChatSearchesOpenSearch:
    """S7-I03: Chat endpoint triggers the search service."""

    @patch("app.services.chat.claude")
    @patch("app.services.chat.search")
    def test_chat_searches_opensearch(self, mock_search, mock_claude, client, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.chat.TEMP_DIR", tmp_path)
        mock_search.return_value = EMPTY_RESULTS
        mock_claude.query.return_value = _make_claude_response("No info found.")

        resp = client.post("/api/chat", json={"message": "What is the deploy strategy?"})

        assert resp.status_code == 200
        mock_search.assert_called_once_with("What is the deploy strategy?")


# ---------------------------------------------------------------------------
# S7-I04: Context file preparation
# ---------------------------------------------------------------------------

class TestChatContextPreparation:
    """S7-I04: Context file is written with search results for Claude."""

    @patch("app.services.chat.claude")
    @patch("app.services.chat.search")
    def test_chat_context_preparation(self, mock_search, mock_claude, client, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.chat.TEMP_DIR", tmp_path)
        mock_search.return_value = SINGLE_RESULT
        mock_claude.query.return_value = _make_claude_response("Answer here.")

        resp = client.post("/api/chat", json={"message": "auth question"})

        assert resp.status_code == 200
        # The prompt passed to Claude should reference the context file
        call_args = mock_claude.query.call_args
        prompt = call_args[0][0]
        assert "context_" in prompt
        assert "auth question" in prompt


# ---------------------------------------------------------------------------
# S7-I05: Response includes citations
# ---------------------------------------------------------------------------

class TestChatResponseIncludesCitations:
    """S7-I05: Response includes citation objects parsed from Claude's text."""

    @patch("app.services.chat.claude")
    @patch("app.services.chat.search")
    def test_chat_response_includes_citations(self, mock_search, mock_claude, client, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.chat.TEMP_DIR", tmp_path)
        mock_search.return_value = SINGLE_RESULT
        mock_claude.query.return_value = _make_claude_response(
            "The team uses Cognito [Auth Meeting @ 2:05]."
        )

        resp = client.post("/api/chat", json={"message": "What auth?"})

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["citations"]) == 1
        citation = data["citations"][0]
        assert citation["video_id"] == "vid-1"
        assert citation["video_title"] == "Auth Meeting"
        assert citation["timestamp"] == 125.0  # 2:05 in seconds


# ---------------------------------------------------------------------------
# S7-I06: Empty search results
# ---------------------------------------------------------------------------

class TestChatEmptySearchResults:
    """S7-I06: No matching segments handled gracefully."""

    @patch("app.services.chat.claude")
    @patch("app.services.chat.search")
    def test_chat_empty_search_results(self, mock_search, mock_claude, client, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.chat.TEMP_DIR", tmp_path)
        mock_search.return_value = EMPTY_RESULTS
        mock_claude.query.return_value = _make_claude_response(
            "I could not find relevant information about that topic."
        )

        resp = client.post("/api/chat", json={"message": "Unknown topic"})

        assert resp.status_code == 200
        data = resp.json()
        assert data["citations"] == []
        assert "message" in data
        assert "conversation_id" in data


# ---------------------------------------------------------------------------
# S7-I07: Claude error returns 500
# ---------------------------------------------------------------------------

class TestChatClaudeError:
    """S7-I07: Claude CLI failure returns HTTP 500."""

    @patch("app.services.chat.claude")
    @patch("app.services.chat.search")
    def test_chat_claude_error(self, mock_search, mock_claude, client, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.chat.TEMP_DIR", tmp_path)
        mock_search.return_value = SINGLE_RESULT
        mock_claude.query.side_effect = ClaudeError("CLI crashed")

        resp = client.post("/api/chat", json={"message": "migrate to Cognito"})

        assert resp.status_code == 500
        assert "unavailable" in resp.json()["detail"].lower()


# ---------------------------------------------------------------------------
# S2-I01: Multiple source citations
# ---------------------------------------------------------------------------

class TestSummaryCitesMultipleSources:
    """S2-I01: Response with multiple video citations."""

    @patch("app.services.chat.claude")
    @patch("app.services.chat.search")
    def test_summary_cites_multiple_sources(self, mock_search, mock_claude, client, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.chat.TEMP_DIR", tmp_path)
        mock_search.return_value = MULTI_RESULTS
        mock_claude.query.return_value = _make_claude_response(
            "Auth was discussed [Auth Meeting @ 2:05] and deployment "
            "was covered [Deploy Review @ 5:00]."
        )

        resp = client.post("/api/chat", json={"message": "Cognito deployment strategy"})

        assert resp.status_code == 200
        data = resp.json()
        assert len(data["citations"]) == 2
        video_ids = {c["video_id"] for c in data["citations"]}
        assert video_ids == {"vid-1", "vid-2"}


# ---------------------------------------------------------------------------
# S2-I02: Content synthesis
# ---------------------------------------------------------------------------

class TestSummarySynthesizesContent:
    """S2-I02: Answer combining information from multiple segments."""

    @patch("app.services.chat.claude")
    @patch("app.services.chat.search")
    def test_summary_synthesizes_content(self, mock_search, mock_claude, client, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.chat.TEMP_DIR", tmp_path)
        mock_search.return_value = MULTI_RESULTS
        mock_claude.query.return_value = _make_claude_response(
            "The project uses Cognito for authentication [Auth Meeting @ 2:05] "
            "and employs a blue-green deployment strategy [Deploy Review @ 5:00]. "
            "Together, these ensure secure and reliable releases."
        )

        resp = client.post("/api/chat", json={"message": "How does the deployment strategy work?"})

        assert resp.status_code == 200
        data = resp.json()
        # Response synthesizes info from both sources
        assert "Cognito" in data["message"]
        assert "blue-green" in data["message"]
        # Both sources are cited
        assert len(data["citations"]) == 2
