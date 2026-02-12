"""Unit tests for chat schemas (S8-U01 and chat validation)."""

import pytest
from pydantic import ValidationError

from app.schemas.chat import ChatRequest, ChatResponse, Citation


class TestCitation:
    """S8-U01: Citation schema validates correctly."""

    def test_citation_valid(self):
        """Citation accepts valid video_id, title, timestamp, text."""
        citation = Citation(
            video_id="vid-123",
            video_title="Auth Meeting",
            timestamp=125.5,
            text="We decided to migrate from Auth0...",
        )
        assert citation.video_id == "vid-123"
        assert citation.video_title == "Auth Meeting"
        assert citation.timestamp == 125.5
        assert citation.text == "We decided to migrate from Auth0..."

    def test_citation_timestamp_zero(self):
        """Citation accepts timestamp of 0."""
        citation = Citation(
            video_id="vid-1", video_title="T", timestamp=0, text="start"
        )
        assert citation.timestamp == 0

    def test_citation_timestamp_negative_rejected(self):
        """Citation rejects negative timestamp."""
        with pytest.raises(ValidationError) as exc_info:
            Citation(
                video_id="vid-1", video_title="T", timestamp=-1.0, text="bad"
            )
        assert "timestamp" in str(exc_info.value)

    def test_citation_missing_fields(self):
        """Citation requires all fields."""
        with pytest.raises(ValidationError):
            Citation(video_id="vid-1", video_title="T")  # missing timestamp and text


class TestChatRequest:
    """Chat request validation tests."""

    def test_valid_new_conversation(self):
        """ChatRequest with message only (new conversation)."""
        req = ChatRequest(message="What auth system do we use?")
        assert req.message == "What auth system do we use?"
        assert req.conversation_id is None

    def test_valid_resume_conversation(self):
        """ChatRequest accepts optional conversation_id."""
        req = ChatRequest(
            message="Tell me more",
            conversation_id="550e8400-e29b-41d4-a716-446655440000",
        )
        assert req.conversation_id == "550e8400-e29b-41d4-a716-446655440000"

    def test_empty_message_rejected(self):
        """ChatRequest rejects empty message."""
        with pytest.raises(ValidationError) as exc_info:
            ChatRequest(message="")
        assert "message" in str(exc_info.value)

    def test_missing_message_rejected(self):
        """ChatRequest requires message field."""
        with pytest.raises(ValidationError):
            ChatRequest()

    def test_conversation_id_none_default(self):
        """conversation_id defaults to None."""
        req = ChatRequest(message="hello")
        assert req.conversation_id is None


class TestChatResponse:
    """Chat response schema tests."""

    def test_response_all_fields(self):
        """ChatResponse includes message, conversation_id, citations."""
        resp = ChatResponse(
            message="Based on the recordings...",
            conversation_id="abc-123",
            citations=[
                Citation(
                    video_id="vid-1",
                    video_title="Auth Meeting",
                    timestamp=125.5,
                    text="We use Cognito",
                )
            ],
        )
        assert resp.message == "Based on the recordings..."
        assert resp.conversation_id == "abc-123"
        assert len(resp.citations) == 1
        assert resp.citations[0].video_title == "Auth Meeting"

    def test_response_empty_citations(self):
        """ChatResponse defaults to empty citations list."""
        resp = ChatResponse(
            message="No info found.",
            conversation_id="abc-123",
        )
        assert resp.citations == []

    def test_response_multiple_citations(self):
        """ChatResponse handles multiple citations."""
        resp = ChatResponse(
            message="Found in two videos...",
            conversation_id="abc-123",
            citations=[
                Citation(
                    video_id="vid-1",
                    video_title="Meeting 1",
                    timestamp=10.0,
                    text="First mention",
                ),
                Citation(
                    video_id="vid-2",
                    video_title="Meeting 2",
                    timestamp=300.0,
                    text="Second mention",
                ),
            ],
        )
        assert len(resp.citations) == 2
