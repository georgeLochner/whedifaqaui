"""Unit tests for document generation service."""

import json
import uuid
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.services.document import (
    build_document_prompt,
    cleanup_context_file,
    extract_title,
    generate_document,
    get_document,
    prepare_document_context,
)


# ---------------------------------------------------------------------------
# extract_title
# ---------------------------------------------------------------------------

class TestExtractTitle:
    """Test title extraction from markdown content."""

    def test_extracts_h1_heading(self):
        """Extracts title from a # heading."""
        content = "# Meeting Summary\n\nSome content here."
        assert extract_title(content) == "Meeting Summary"

    def test_extracts_h2_heading(self):
        """Extracts title from ## heading if it's first."""
        content = "## Section Title\n\nContent."
        assert extract_title(content) == "Section Title"

    def test_uses_first_line_if_no_heading(self):
        """Falls back to first non-empty line when no heading found."""
        content = "This is a plain text document.\n\nMore content."
        assert extract_title(content) == "This is a plain text document."

    def test_skips_empty_lines(self):
        """Skips leading empty lines to find title."""
        content = "\n\n# Actual Title\n\nContent."
        assert extract_title(content) == "Actual Title"

    def test_fallback_for_empty_content(self):
        """Returns default title for empty content."""
        assert extract_title("") == "Generated Document"
        assert extract_title("\n\n\n") == "Generated Document"

    def test_truncates_long_title(self):
        """Title is truncated to 255 characters max."""
        long_line = "A" * 500
        title = extract_title(long_line)
        assert len(title) <= 255


# ---------------------------------------------------------------------------
# build_document_prompt
# ---------------------------------------------------------------------------

class TestBuildDocumentPrompt:
    """Test prompt construction."""

    def test_prompt_contains_file_path(self):
        """Prompt includes the source file path."""
        prompt = build_document_prompt("Summarize", "/data/temp/ctx.json")
        assert "/data/temp/ctx.json" in prompt

    def test_prompt_contains_request(self):
        """Prompt includes the user request."""
        prompt = build_document_prompt("Summarize the auth discussion", "/tmp/f.json")
        assert "Summarize the auth discussion" in prompt

    def test_prompt_has_instructions(self):
        """Prompt includes document generation instructions."""
        prompt = build_document_prompt("test", "/tmp/f.json")
        assert "READ THE SOURCE FILE" in prompt
        assert "[MM:SS]" in prompt
        assert "# Title" in prompt


# ---------------------------------------------------------------------------
# prepare_document_context
# ---------------------------------------------------------------------------

class TestPrepareDocumentContext:
    """Test transcript fetching and context file creation."""

    def test_writes_context_file(self, tmp_path, monkeypatch):
        """Context file is created with transcript content."""
        monkeypatch.setattr("app.services.document.TEMP_DIR", tmp_path)

        vid_id = uuid.uuid4()

        mock_transcript = MagicMock()
        mock_transcript.video_id = vid_id
        mock_transcript.full_text = "This is the transcript content."

        mock_video = MagicMock()
        mock_video.id = vid_id
        mock_video.title = "Auth Meeting"

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.side_effect = [[mock_transcript], [mock_video]]
        mock_db.query.return_value = mock_query

        path, video_ids = prepare_document_context([str(vid_id)], mock_db)

        assert Path(path).exists()
        data = json.loads(Path(path).read_text())
        assert len(data["transcripts"]) == 1
        assert data["transcripts"][0]["video_id"] == str(vid_id)
        assert data["transcripts"][0]["video_title"] == "Auth Meeting"
        assert data["transcripts"][0]["text"] == "This is the transcript content."
        assert video_ids == [vid_id]

    def test_creates_temp_directory(self, tmp_path, monkeypatch):
        """TEMP_DIR is created if it doesn't exist."""
        nested = tmp_path / "sub" / "dir"
        monkeypatch.setattr("app.services.document.TEMP_DIR", nested)

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        path, _ = prepare_document_context(["00000000-0000-0000-0000-000000000001"], mock_db)

        assert nested.exists()
        assert Path(path).exists()

    def test_handles_no_video_ids(self, tmp_path, monkeypatch):
        """Fetches all transcripts when video_ids is None."""
        monkeypatch.setattr("app.services.document.TEMP_DIR", tmp_path)

        mock_db = MagicMock()
        mock_query = MagicMock()
        # When video_ids is None, query.all() is called directly (no filter)
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        path, video_ids = prepare_document_context(None, mock_db)

        assert Path(path).exists()
        assert video_ids == []


# ---------------------------------------------------------------------------
# cleanup_context_file
# ---------------------------------------------------------------------------

class TestCleanupContextFile:
    """Test context file cleanup."""

    def test_deletes_existing_file(self, tmp_path):
        """Temp file is deleted."""
        f = tmp_path / "doc_context_test.json"
        f.write_text("{}")
        cleanup_context_file(str(f))
        assert not f.exists()

    def test_missing_file_no_error(self, tmp_path):
        """No error when file doesn't exist."""
        cleanup_context_file(str(tmp_path / "nonexistent.json"))


# ---------------------------------------------------------------------------
# generate_document - full flow
# ---------------------------------------------------------------------------

class TestGenerateDocument:
    """Test the full generate_document orchestration."""

    @patch("app.services.document.claude")
    def test_calls_claude_with_correct_prompt(self, mock_claude, tmp_path, monkeypatch):
        """generate_document calls claude.query with a prompt containing the request."""
        monkeypatch.setattr("app.services.document.TEMP_DIR", tmp_path)

        mock_claude.query.return_value = MagicMock(
            result="# Summary\n\nKey points from the meeting.",
            conversation_id="conv-123",
        )

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        from app.schemas.document import DocumentRequest
        req = DocumentRequest(request="Summarize the meeting")

        generate_document(req, "session-1", mock_db)

        mock_claude.query.assert_called_once()
        call_args = mock_claude.query.call_args
        prompt = call_args[0][0]
        assert "Summarize the meeting" in prompt
        assert "READ THE SOURCE FILE" in prompt

    @patch("app.services.document.claude")
    def test_extracts_title_from_claude_response(self, mock_claude, tmp_path, monkeypatch):
        """Title is extracted from the first heading in Claude's response."""
        monkeypatch.setattr("app.services.document.TEMP_DIR", tmp_path)

        mock_claude.query.return_value = MagicMock(
            result="# Auth Discussion Summary\n\nThe team decided...",
            conversation_id="conv-456",
        )

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        from app.schemas.document import DocumentRequest
        req = DocumentRequest(request="Summarize auth discussion")

        doc = generate_document(req, None, mock_db)

        # Check the GeneratedDocument was created with correct title
        add_call = mock_db.add.call_args[0][0]
        assert add_call.title == "Auth Discussion Summary"

    @patch("app.services.document.claude")
    def test_saves_document_to_database(self, mock_claude, tmp_path, monkeypatch):
        """Document is saved to database with db.add/commit/refresh."""
        monkeypatch.setattr("app.services.document.TEMP_DIR", tmp_path)

        mock_claude.query.return_value = MagicMock(
            result="# Summary\n\nContent.",
            conversation_id="conv-789",
        )

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        from app.schemas.document import DocumentRequest
        req = DocumentRequest(request="Summarize")

        generate_document(req, "session-1", mock_db)

        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    @patch("app.services.document.claude")
    def test_cleans_up_context_file(self, mock_claude, tmp_path, monkeypatch):
        """Context file is cleaned up after generation."""
        monkeypatch.setattr("app.services.document.TEMP_DIR", tmp_path)

        mock_claude.query.return_value = MagicMock(
            result="# Doc\n\nContent.",
            conversation_id="conv-1",
        )

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        from app.schemas.document import DocumentRequest
        req = DocumentRequest(request="Test")

        generate_document(req, None, mock_db)

        # No context files should remain
        assert list(tmp_path.glob("doc_context_*.json")) == []

    @patch("app.services.document.claude")
    def test_cleans_up_on_error(self, mock_claude, tmp_path, monkeypatch):
        """Context file is cleaned up even when Claude raises an error."""
        monkeypatch.setattr("app.services.document.TEMP_DIR", tmp_path)

        from app.services.claude import ClaudeError
        mock_claude.query.side_effect = ClaudeError("CLI failed")

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.all.return_value = []
        mock_db.query.return_value = mock_query

        from app.schemas.document import DocumentRequest
        req = DocumentRequest(request="Test")

        with pytest.raises(ClaudeError):
            generate_document(req, None, mock_db)

        # Context file should still be cleaned up
        assert list(tmp_path.glob("doc_context_*.json")) == []


# ---------------------------------------------------------------------------
# get_document
# ---------------------------------------------------------------------------

class TestGetDocument:
    """Test document retrieval by ID."""

    def test_returns_document_when_found(self):
        """get_document returns the document when it exists."""
        doc_id = uuid.uuid4()
        mock_doc = MagicMock()
        mock_doc.id = doc_id

        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = mock_doc
        mock_db.query.return_value = mock_query

        result = get_document(doc_id, mock_db)

        assert result is mock_doc

    def test_returns_none_when_not_found(self):
        """get_document returns None when document doesn't exist."""
        mock_db = MagicMock()
        mock_query = MagicMock()
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        mock_db.query.return_value = mock_query

        result = get_document(uuid.uuid4(), mock_db)

        assert result is None
