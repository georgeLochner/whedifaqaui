"""Unit tests for document schemas (S10-U01 to S10-U04)."""

import uuid
from datetime import datetime, timezone

import pytest
from pydantic import ValidationError

from app.schemas.document import DocumentDetail, DocumentRequest, DocumentResponse


class TestDocumentSchemaValidation:
    """S10-U01: Document schema validation."""

    def test_valid_request(self):
        """DocumentRequest accepts valid data."""
        req = DocumentRequest(
            request="Summarize the meeting",
            source_video_ids=["vid-123"],
            format="markdown",
        )
        assert req.request == "Summarize the meeting"
        assert req.source_video_ids == ["vid-123"]
        assert req.format == "markdown"

    def test_request_defaults(self):
        """DocumentRequest applies defaults for optional fields."""
        req = DocumentRequest(request="Summarize")
        assert req.source_video_ids is None
        assert req.format == "markdown"

    def test_empty_request_rejected(self):
        """DocumentRequest rejects empty request string."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentRequest(request="")
        assert "request" in str(exc_info.value)

    def test_missing_request_rejected(self):
        """DocumentRequest requires request field."""
        with pytest.raises(ValidationError):
            DocumentRequest()


class TestDocumentIdGeneration:
    """S10-U02: Document ID generation — UUID format validated."""

    def test_response_accepts_valid_uuid(self):
        """DocumentResponse accepts a valid UUID id."""
        doc_id = uuid.uuid4()
        resp = DocumentResponse(
            id=doc_id,
            title="Summary",
            preview="This document covers...",
            source_count=2,
            created_at=datetime.now(timezone.utc),
        )
        assert resp.id == doc_id

    def test_detail_accepts_valid_uuid(self):
        """DocumentDetail accepts a valid UUID id."""
        doc_id = uuid.uuid4()
        detail = DocumentDetail(
            id=doc_id,
            title="Summary",
            content="# Summary\n\nContent here.",
            source_video_ids=[uuid.uuid4()],
            created_at=datetime.now(timezone.utc),
        )
        assert detail.id == doc_id

    def test_response_rejects_invalid_uuid(self):
        """DocumentResponse rejects invalid UUID format."""
        with pytest.raises(ValidationError) as exc_info:
            DocumentResponse(
                id="not-a-uuid",
                title="Summary",
                preview="preview",
                source_count=0,
                created_at=datetime.now(timezone.utc),
            )
        assert "id" in str(exc_info.value)


class TestDocumentContentMarkdown:
    """S10-U03: Document content is valid markdown — parses without error."""

    def test_content_accepts_markdown(self):
        """DocumentDetail accepts markdown content string."""
        markdown = (
            "# Meeting Summary\n\n"
            "## Key Points\n\n"
            "- Feature discussion at [03:45]\n"
            "- **Bold** and *italic* text\n"
            "- Code: `function()`\n"
        )
        detail = DocumentDetail(
            id=uuid.uuid4(),
            title="Meeting Summary",
            content=markdown,
            created_at=datetime.now(timezone.utc),
        )
        assert detail.content == markdown
        assert "# Meeting Summary" in detail.content

    def test_content_preserves_multiline(self):
        """DocumentDetail preserves multiline markdown content."""
        content = "Line 1\n\nLine 2\n\n> Blockquote\n"
        detail = DocumentDetail(
            id=uuid.uuid4(),
            title="Test",
            content=content,
            created_at=datetime.now(timezone.utc),
        )
        assert "\n" in detail.content
        assert detail.content.count("\n") == content.count("\n")


class TestDocumentSourceTracking:
    """S10-U04: Source video/segment IDs stored — arrays populated."""

    def test_source_video_ids_populated(self):
        """DocumentDetail stores source video IDs."""
        vid_id1 = uuid.uuid4()
        vid_id2 = uuid.uuid4()
        detail = DocumentDetail(
            id=uuid.uuid4(),
            title="Summary",
            content="# Summary",
            source_video_ids=[vid_id1, vid_id2],
            created_at=datetime.now(timezone.utc),
        )
        assert len(detail.source_video_ids) == 2
        assert vid_id1 in detail.source_video_ids
        assert vid_id2 in detail.source_video_ids

    def test_source_video_ids_defaults_empty(self):
        """DocumentDetail defaults to empty source_video_ids list."""
        detail = DocumentDetail(
            id=uuid.uuid4(),
            title="Summary",
            content="# Summary",
            created_at=datetime.now(timezone.utc),
        )
        assert detail.source_video_ids == []

    def test_response_source_count(self):
        """DocumentResponse tracks source count."""
        resp = DocumentResponse(
            id=uuid.uuid4(),
            title="Summary",
            preview="This document...",
            source_count=3,
            created_at=datetime.now(timezone.utc),
        )
        assert resp.source_count == 3
