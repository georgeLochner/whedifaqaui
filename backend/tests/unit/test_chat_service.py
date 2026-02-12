"""Unit tests for chat service (S7-U08–U12, S2-U01–U03, S8-U02)."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.schemas.chat import ChatResponse, Citation
from app.schemas.search import SearchResponse, SearchResult
from app.services.chat import (
    CITATION_PATTERN,
    MAX_CONTEXT_CHARS,
    _has_keyword_overlap,
    _mmss_to_seconds,
    build_prompt,
    cleanup_context_file,
    deduplicate_citations,
    extract_citations,
    handle_chat_message,
    prepare_context_file,
    truncate_context,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_search_result(**overrides) -> SearchResult:
    """Create a SearchResult with sensible defaults."""
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


# ---------------------------------------------------------------------------
# S7-U08: Context file creation
# ---------------------------------------------------------------------------

class TestContextFileCreation:
    """S7-U08: prepare_context_file writes valid JSON to disk."""

    def test_context_file_creation(self, tmp_path, monkeypatch):
        """Context file is created with correct JSON structure."""
        monkeypatch.setattr("app.services.chat.TEMP_DIR", tmp_path)

        segments = [_make_search_result()]
        path = prepare_context_file(segments, "What auth system?")

        assert Path(path).exists()
        data = json.loads(Path(path).read_text())
        assert data["query"] == "What auth system?"
        assert len(data["segments"]) == 1
        seg = data["segments"][0]
        assert seg["video_id"] == "vid-1"
        assert seg["video_title"] == "Auth Meeting"
        assert seg["timestamp"] == 125.5
        assert seg["text"] == "We decided to migrate from Auth0 to Cognito."
        assert seg["speaker"] == "SPEAKER_00"
        assert seg["recording_date"] == "2023-01-05"

    def test_context_file_creates_directory(self, tmp_path, monkeypatch):
        """TEMP_DIR is created if it doesn't exist."""
        nested = tmp_path / "sub" / "dir"
        monkeypatch.setattr("app.services.chat.TEMP_DIR", nested)

        segments = [_make_search_result()]
        path = prepare_context_file(segments, "query")

        assert nested.exists()
        assert Path(path).exists()


# ---------------------------------------------------------------------------
# S7-U09: Context file cleanup
# ---------------------------------------------------------------------------

class TestContextFileCleanup:
    """S7-U09: cleanup_context_file removes temp files."""

    def test_context_file_cleanup(self, tmp_path):
        """Temp file is deleted after cleanup."""
        f = tmp_path / "context_test.json"
        f.write_text("{}")

        cleanup_context_file(str(f))
        assert not f.exists()

    def test_cleanup_missing_file_no_error(self, tmp_path):
        """Cleanup does not raise when file is already gone."""
        cleanup_context_file(str(tmp_path / "nonexistent.json"))


# ---------------------------------------------------------------------------
# S7-U10: Prompt construction
# ---------------------------------------------------------------------------

class TestPromptConstruction:
    """S7-U10: build_prompt produces prompt with file path reference."""

    def test_prompt_construction(self):
        """Prompt contains both the file path and the question."""
        prompt = build_prompt("What auth?", "/data/temp/context_abc.json")

        assert "/data/temp/context_abc.json" in prompt
        assert "What auth?" in prompt

    def test_prompt_uses_template(self):
        """Prompt follows the QUICK_MODE_PROMPT template structure."""
        prompt = build_prompt("Tell me more", "/tmp/ctx.json")

        assert "READ THE CONTEXT FILE" in prompt
        assert "User question:" in prompt


# ---------------------------------------------------------------------------
# S7-U11: Citation extraction
# ---------------------------------------------------------------------------

class TestCitationExtraction:
    """S7-U11: extract_citations parses [Video Title @ MM:SS] citations."""

    def test_citation_extraction(self):
        """Citations are extracted with correct video_id and timestamp."""
        text = (
            "The team discussed auth migration [Auth Meeting @ 2:05] "
            "and later revisited it [Deploy Review @ 10:30]."
        )
        results = [
            _make_search_result(video_id="vid-1", video_title="Auth Meeting"),
            _make_search_result(
                video_id="vid-2",
                video_title="Deploy Review",
                segment_id="seg-2",
                text="Revisited the auth decision.",
                start_time=630.0,
            ),
        ]

        citations = extract_citations(text, results)

        assert len(citations) == 2
        assert citations[0].video_id == "vid-1"
        assert citations[0].video_title == "Auth Meeting"
        assert citations[0].timestamp == 125.0  # 2:05
        assert citations[1].video_id == "vid-2"
        assert citations[1].video_title == "Deploy Review"
        assert citations[1].timestamp == 630.0  # 10:30

    def test_citation_extraction_single_digit_minute(self):
        """Citation with single-digit minute is parsed correctly."""
        text = "Mentioned here [Some Video @ 0:45]."
        results = [_make_search_result(video_title="Some Video")]

        citations = extract_citations(text, results)

        assert len(citations) == 1
        assert citations[0].timestamp == 45.0


# ---------------------------------------------------------------------------
# S7-U12: No citations in response
# ---------------------------------------------------------------------------

class TestCitationExtractionNoCitations:
    """S7-U12: Handle response text with no citation patterns."""

    def test_citation_extraction_no_citations(self):
        """Returns empty list when response has no citation patterns."""
        text = "I could not find any relevant information about that topic."
        results = [_make_search_result()]

        citations = extract_citations(text, results)

        assert citations == []

    def test_citation_extraction_unknown_video(self):
        """Citations referencing unknown videos are skipped when multiple videos exist."""
        text = "See [Unknown Video @ 1:00] for details."
        results = [
            _make_search_result(video_id="vid-1", video_title="Known Video"),
            _make_search_result(video_id="vid-2", video_title="Another Video", segment_id="seg-2"),
        ]

        citations = extract_citations(text, results)

        assert citations == []


# ---------------------------------------------------------------------------
# S2-U01: Multi-video context building
# ---------------------------------------------------------------------------

class TestMultiVideoContext:
    """S2-U01: Context includes segments from multiple videos."""

    def test_multi_video_context_building(self, tmp_path, monkeypatch):
        """Context file includes segments from different videos."""
        monkeypatch.setattr("app.services.chat.TEMP_DIR", tmp_path)

        segments = [
            _make_search_result(video_id="vid-1", video_title="Auth Meeting"),
            _make_search_result(
                video_id="vid-2",
                video_title="Deploy Review",
                segment_id="seg-2",
                text="Deployment pipeline overview.",
                start_time=300.0,
            ),
            _make_search_result(
                video_id="vid-3",
                video_title="Sprint Retro",
                segment_id="seg-3",
                text="Discussed improvements.",
                start_time=60.0,
            ),
        ]

        path = prepare_context_file(segments, "project overview")
        data = json.loads(Path(path).read_text())

        video_ids = {seg["video_id"] for seg in data["segments"]}
        assert video_ids == {"vid-1", "vid-2", "vid-3"}


# ---------------------------------------------------------------------------
# S2-U02: Context truncation
# ---------------------------------------------------------------------------

class TestContextTruncation:
    """S2-U02: Long context is truncated under the character limit."""

    def test_context_truncation(self):
        """Segments exceeding max_chars are dropped."""
        segments = [
            {"text": "A" * 100, "video_id": "v1"},
            {"text": "B" * 100, "video_id": "v2"},
            {"text": "C" * 100, "video_id": "v3"},
        ]

        result = truncate_context(segments, max_chars=250)

        assert len(result) == 2
        assert result[0]["video_id"] == "v1"
        assert result[1]["video_id"] == "v2"

    def test_truncation_all_fit(self):
        """All segments returned when under limit."""
        segments = [
            {"text": "short", "video_id": "v1"},
            {"text": "also short", "video_id": "v2"},
        ]

        result = truncate_context(segments, max_chars=1000)

        assert len(result) == 2

    def test_truncation_empty(self):
        """Empty segment list returns empty."""
        assert truncate_context([], max_chars=100) == []

    def test_context_file_applies_truncation(self, tmp_path, monkeypatch):
        """prepare_context_file truncates segments exceeding MAX_CONTEXT_CHARS."""
        monkeypatch.setattr("app.services.chat.TEMP_DIR", tmp_path)
        monkeypatch.setattr("app.services.chat.MAX_CONTEXT_CHARS", 200)

        segments = [
            _make_search_result(
                segment_id=f"seg-{i}",
                text="X" * 150,
                video_id=f"vid-{i}",
            )
            for i in range(5)
        ]

        path = prepare_context_file(segments, "query")
        data = json.loads(Path(path).read_text())

        assert len(data["segments"]) < 5


# ---------------------------------------------------------------------------
# S2-U03: Source formatting
# ---------------------------------------------------------------------------

class TestSourceFormatting:
    """S2-U03: Sources are formatted correctly in the context file."""

    def test_source_formatting(self, tmp_path, monkeypatch):
        """Each segment includes all required source fields."""
        monkeypatch.setattr("app.services.chat.TEMP_DIR", tmp_path)

        segments = [
            _make_search_result(
                video_id="vid-1",
                video_title="Auth Meeting",
                start_time=125.5,
                speaker="SPEAKER_00",
                recording_date="2023-01-05",
            )
        ]

        path = prepare_context_file(segments, "auth question")
        data = json.loads(Path(path).read_text())
        seg = data["segments"][0]

        assert set(seg.keys()) == {
            "video_id",
            "video_title",
            "timestamp",
            "text",
            "speaker",
            "recording_date",
        }


# ---------------------------------------------------------------------------
# S8-U02: Result deduplication
# ---------------------------------------------------------------------------

class TestResultDeduplication:
    """S8-U02: Duplicate citations (same video_id + timestamp) are removed."""

    def test_result_deduplication(self):
        """Duplicate citations are removed, first occurrence kept."""
        citations = [
            Citation(video_id="vid-1", video_title="Auth Meeting", timestamp=125.0, text="First"),
            Citation(video_id="vid-1", video_title="Auth Meeting", timestamp=125.0, text="Duplicate"),
            Citation(video_id="vid-2", video_title="Deploy Review", timestamp=300.0, text="Other"),
        ]

        result = deduplicate_citations(citations)

        assert len(result) == 2
        assert result[0].text == "First"
        assert result[1].video_id == "vid-2"

    def test_dedup_different_timestamps(self):
        """Same video_id but different timestamps are kept."""
        citations = [
            Citation(video_id="vid-1", video_title="Auth Meeting", timestamp=60.0, text="A"),
            Citation(video_id="vid-1", video_title="Auth Meeting", timestamp=120.0, text="B"),
        ]

        result = deduplicate_citations(citations)

        assert len(result) == 2


# ---------------------------------------------------------------------------
# handle_chat_message orchestration
# ---------------------------------------------------------------------------

class TestHandleChatMessage:
    """Integration-style unit tests for the orchestration function."""

    @patch("app.services.chat.search")
    @patch("app.services.chat.claude")
    def test_handle_chat_message_full_flow(self, mock_claude, mock_search, tmp_path, monkeypatch):
        """Full flow: search → context → Claude → citations → cleanup."""
        monkeypatch.setattr("app.services.chat.TEMP_DIR", tmp_path)

        mock_search.return_value = SearchResponse(
            count=1,
            results=[_make_search_result()],
        )

        mock_claude.query.return_value = MagicMock(
            result="The team uses Cognito [Auth Meeting @ 2:05].",
            conversation_id="conv-123",
        )

        response = handle_chat_message("What auth system?")

        assert isinstance(response, ChatResponse)
        assert response.conversation_id == "conv-123"
        assert "Cognito" in response.message
        assert len(response.citations) == 1
        assert response.citations[0].video_title == "Auth Meeting"

        # Temp file should be cleaned up
        assert list(tmp_path.glob("context_*.json")) == []

    @patch("app.services.chat.search")
    @patch("app.services.chat.claude")
    def test_handle_chat_empty_search(self, mock_claude, mock_search, tmp_path, monkeypatch):
        """Short-circuit with canned response when search returns no results."""
        monkeypatch.setattr("app.services.chat.TEMP_DIR", tmp_path)

        mock_search.return_value = SearchResponse(count=0, results=[])

        response = handle_chat_message("Unknown topic")

        assert response.citations == []
        assert "couldn't find any relevant information" in response.message
        mock_claude.query.assert_not_called()

    @patch("app.services.chat.search")
    @patch("app.services.chat.claude")
    def test_handle_chat_cleanup_on_error(self, mock_claude, mock_search, tmp_path, monkeypatch):
        """Temp file is cleaned up even when Claude raises an error."""
        monkeypatch.setattr("app.services.chat.TEMP_DIR", tmp_path)

        # Use text that contains the query keyword so keyword overlap passes
        mock_search.return_value = SearchResponse(
            count=1, results=[_make_search_result(text="We discussed migration details.")]
        )

        from app.services.claude import ClaudeError
        mock_claude.query.side_effect = ClaudeError("CLI failed")

        with pytest.raises(ClaudeError):
            handle_chat_message("migration details")

        # Temp file should still be cleaned up
        assert list(tmp_path.glob("context_*.json")) == []

    @patch("app.services.chat.search")
    @patch("app.services.chat.claude")
    def test_handle_chat_passes_conversation_id(self, mock_claude, mock_search, tmp_path, monkeypatch):
        """conversation_id is passed through to Claude."""
        monkeypatch.setattr("app.services.chat.TEMP_DIR", tmp_path)

        mock_search.return_value = SearchResponse(count=0, results=[])
        mock_claude.query.return_value = MagicMock(
            result="Response", conversation_id="existing-conv"
        )

        handle_chat_message("follow up", conversation_id="existing-conv")

        _, kwargs = mock_claude.query.call_args
        assert kwargs["conversation_id"] == "existing-conv"


# ---------------------------------------------------------------------------
# Keyword overlap
# ---------------------------------------------------------------------------

class TestKeywordOverlap:
    """Tests for _has_keyword_overlap relevance check."""

    def test_relevant_query(self):
        results = [_make_search_result(text="The permissions filter was added to Backdrop 1.24.")]
        assert _has_keyword_overlap("permissions filter", results) is True

    def test_irrelevant_query(self):
        results = [_make_search_result(text="The permissions filter was added to Backdrop 1.24.")]
        assert _has_keyword_overlap("quantum computing", results) is False

    def test_all_stopwords_returns_true(self):
        results = [_make_search_result(text="Some text.")]
        assert _has_keyword_overlap("what did we do?", results) is True

    def test_partial_overlap(self):
        results = [_make_search_result(text="The team discussed deployment strategies.")]
        assert _has_keyword_overlap("deployment and quantum computing", results) is True


# ---------------------------------------------------------------------------
# Utility tests
# ---------------------------------------------------------------------------

class TestMmssToSeconds:
    """Tests for MM:SS to seconds conversion."""

    def test_basic_conversion(self):
        assert _mmss_to_seconds("2:05") == 125.0

    def test_zero(self):
        assert _mmss_to_seconds("0:00") == 0.0

    def test_ten_minutes(self):
        assert _mmss_to_seconds("10:30") == 630.0
