"""Integration tests for the Document API endpoints.

Test IDs covered:
  S10-I01  test_create_document_endpoint
  S10-I02  test_get_document_endpoint
  S10-I03  test_download_document_endpoint
  S10-I04  test_document_stored_in_database
  S10-I05  test_document_generation_uses_claude
  S10-I06  test_document_has_citations
"""

from unittest.mock import MagicMock, patch

import pytest
from sqlalchemy.orm import Session

from app.models.document import GeneratedDocument
from app.services.claude import ClaudeResponse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

MOCK_MARKDOWN = (
    "# Backdrop 1.24 Features Summary\n\n"
    "## Key Features\n\n"
    "The team discussed several new features for Backdrop 1.24:\n\n"
    "- Back-to-site button was contributed by a community member [03:45]\n"
    "- Layout builder improvements were demonstrated [12:30]\n"
    "- Performance optimizations reduced page load time [25:15]\n\n"
    "## Conclusion\n\n"
    "Overall, the 1.24 release brings significant improvements."
)


def _mock_claude_response(text: str = MOCK_MARKDOWN) -> ClaudeResponse:
    return ClaudeResponse(result=text, conversation_id="conv-doc-123")


# ---------------------------------------------------------------------------
# S10-I01: POST /api/documents creates document
# ---------------------------------------------------------------------------

class TestCreateDocumentEndpoint:
    """S10-I01: POST /api/documents creates document, returns id and preview."""

    @patch("app.services.document.claude")
    def test_create_document_endpoint(self, mock_claude, client, db, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.document.TEMP_DIR", tmp_path)
        mock_claude.query.return_value = _mock_claude_response()

        resp = client.post("/api/documents", json={
            "request": "Summarize the Backdrop 1.24 features discussion",
        })

        assert resp.status_code == 200
        data = resp.json()
        assert "id" in data
        assert data["title"] == "Backdrop 1.24 Features Summary"
        assert "preview" in data
        assert len(data["preview"]) <= 100
        assert "created_at" in data


# ---------------------------------------------------------------------------
# S10-I02: GET /api/documents/{id} returns content
# ---------------------------------------------------------------------------

class TestGetDocumentEndpoint:
    """S10-I02: GET /api/documents/{id} returns full markdown content."""

    @patch("app.services.document.claude")
    def test_get_document_endpoint(self, mock_claude, client, db, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.document.TEMP_DIR", tmp_path)
        mock_claude.query.return_value = _mock_claude_response()

        # Create a document first
        create_resp = client.post("/api/documents", json={
            "request": "Summarize features",
        })
        doc_id = create_resp.json()["id"]

        # Retrieve it
        resp = client.get(f"/api/documents/{doc_id}")

        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == doc_id
        assert data["title"] == "Backdrop 1.24 Features Summary"
        assert "# Backdrop 1.24 Features Summary" in data["content"]
        assert "Layout builder" in data["content"]

    def test_get_nonexistent_document_returns_404(self, client, db):
        resp = client.get("/api/documents/00000000-0000-0000-0000-000000000001")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# S10-I03: GET /api/documents/{id}/download returns file attachment
# ---------------------------------------------------------------------------

class TestDownloadDocumentEndpoint:
    """S10-I03: GET /api/documents/{id}/download returns file attachment."""

    @patch("app.services.document.claude")
    def test_download_document_endpoint(self, mock_claude, client, db, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.document.TEMP_DIR", tmp_path)
        mock_claude.query.return_value = _mock_claude_response()

        # Create a document first
        create_resp = client.post("/api/documents", json={
            "request": "Summarize features",
        })
        doc_id = create_resp.json()["id"]

        # Download it
        resp = client.get(f"/api/documents/{doc_id}/download")

        assert resp.status_code == 200
        assert resp.headers["content-type"] == "text/markdown; charset=utf-8"
        assert "attachment" in resp.headers["content-disposition"]
        assert ".md" in resp.headers["content-disposition"]
        assert "# Backdrop 1.24 Features Summary" in resp.text

    def test_download_nonexistent_returns_404(self, client, db):
        resp = client.get("/api/documents/00000000-0000-0000-0000-000000000001/download")
        assert resp.status_code == 404


# ---------------------------------------------------------------------------
# S10-I04: Document stored in database
# ---------------------------------------------------------------------------

class TestDocumentStoredInDatabase:
    """S10-I04: After POST, row exists in generated_documents table."""

    @patch("app.services.document.claude")
    def test_document_stored_in_database(self, mock_claude, client, db, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.document.TEMP_DIR", tmp_path)
        mock_claude.query.return_value = _mock_claude_response()

        create_resp = client.post("/api/documents", json={
            "request": "Summarize the meeting",
        })
        doc_id = create_resp.json()["id"]

        # Query the database directly
        doc = db.query(GeneratedDocument).filter(
            GeneratedDocument.id == doc_id
        ).first()

        assert doc is not None
        assert doc.title == "Backdrop 1.24 Features Summary"
        assert "Backdrop 1.24" in doc.content


# ---------------------------------------------------------------------------
# S10-I05: Claude wrapper invoked
# ---------------------------------------------------------------------------

class TestDocumentGenerationUsesClaude:
    """S10-I05: Claude wrapper is invoked during generation."""

    @patch("app.services.document.claude")
    def test_document_generation_uses_claude(self, mock_claude, client, db, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.document.TEMP_DIR", tmp_path)
        mock_claude.query.return_value = _mock_claude_response()

        client.post("/api/documents", json={
            "request": "Summarize the features",
        })

        mock_claude.query.assert_called_once()
        call_args = mock_claude.query.call_args
        prompt = call_args[0][0]
        assert "Summarize the features" in prompt
        assert "READ THE SOURCE FILE" in prompt


# ---------------------------------------------------------------------------
# S10-I06: Document has citations
# ---------------------------------------------------------------------------

class TestDocumentHasCitations:
    """S10-I06: Generated document contains [MM:SS] format citations."""

    @patch("app.services.document.claude")
    def test_document_has_citations(self, mock_claude, client, db, tmp_path, monkeypatch):
        monkeypatch.setattr("app.services.document.TEMP_DIR", tmp_path)
        mock_claude.query.return_value = _mock_claude_response()

        create_resp = client.post("/api/documents", json={
            "request": "Summarize features",
        })
        doc_id = create_resp.json()["id"]

        # Get full content
        resp = client.get(f"/api/documents/{doc_id}")
        content = resp.json()["content"]

        # Verify [MM:SS] citations exist
        import re
        citation_pattern = re.compile(r"\[\d{1,2}:\d{2}\]")
        citations = citation_pattern.findall(content)
        assert len(citations) >= 1, f"Expected [MM:SS] citations in content, found none"
