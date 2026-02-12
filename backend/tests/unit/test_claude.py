"""Unit tests for Claude wrapper module (S7-U01 through S7-U07)."""

import subprocess
import uuid
from unittest.mock import patch, MagicMock

import pytest

from app.services.claude import ClaudeService, ClaudeResponse, ClaudeError


@pytest.fixture
def service():
    return ClaudeService(cli_path="claude")


class TestClaudeCommandConstruction:
    """S7-U01, S7-U02: Verify CLI command construction."""

    def test_claude_command_construction_new(self, service):
        """S7-U01: Build command for new conversation uses --session-id."""
        with patch("app.services.claude.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="response text\n", stderr=""
            )
            with patch("app.services.claude.uuid.uuid4") as mock_uuid:
                mock_uuid.return_value = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
                service.query("test message")

            args = mock_run.call_args
            cmd = args[0][0]
            assert cmd == [
                "claude",
                "--session-id", "550e8400-e29b-41d4-a716-446655440000",
                "-p", "test message",
            ]

    def test_claude_command_construction_resume(self, service):
        """S7-U02: Build command for resumed conversation uses --resume."""
        conv_id = "550e8400-e29b-41d4-a716-446655440000"
        with patch("app.services.claude.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="response text\n", stderr=""
            )
            service.query("follow-up question", conversation_id=conv_id)

            args = mock_run.call_args
            cmd = args[0][0]
            assert cmd == [
                "claude",
                "--resume", conv_id,
                "-p", "follow-up question",
            ]


class TestClaudeResponseParsing:
    """S7-U03: Verify response parsing."""

    def test_claude_response_parsing(self, service):
        """S7-U03: Parse stdout to ClaudeResponse with stripped text."""
        with patch("app.services.claude.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0,
                stdout="  Based on the recordings, you use AWS Cognito.  \n",
                stderr=""
            )
            response = service.query("test", conversation_id="some-id")

            assert isinstance(response, ClaudeResponse)
            assert response.result == "Based on the recordings, you use AWS Cognito."
            assert response.conversation_id == "some-id"


class TestClaudeErrorHandling:
    """S7-U04, S7-U05: Verify error and timeout handling."""

    def test_claude_error_handling(self, service):
        """S7-U04: Handle non-zero exit code by raising ClaudeError."""
        with patch("app.services.claude.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=1, stdout="", stderr="CLI crashed"
            )
            with pytest.raises(ClaudeError) as exc_info:
                service.query("test", conversation_id="some-id")

            assert "CLI error (code 1)" in str(exc_info.value)
            assert "CLI crashed" in str(exc_info.value)

    def test_claude_timeout_handling(self, service):
        """S7-U05: Handle subprocess timeout by re-raising TimeoutExpired."""
        with patch("app.services.claude.subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired(
                cmd=["claude"], timeout=120
            )
            with pytest.raises(subprocess.TimeoutExpired):
                service.query("test", conversation_id="some-id", timeout=120)


class TestConversationIdManagement:
    """S7-U06, S7-U07: Verify conversation ID generation and preservation."""

    def test_conversation_id_generation(self, service):
        """S7-U06: New UUID generated when none provided."""
        with patch("app.services.claude.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="response\n", stderr=""
            )
            response = service.query("test message")

            # Should be a valid UUID v4
            parsed = uuid.UUID(response.conversation_id)
            assert parsed.version == 4

    def test_conversation_id_preserved(self, service):
        """S7-U07: Existing ID used when provided."""
        existing_id = "550e8400-e29b-41d4-a716-446655440000"
        with patch("app.services.claude.subprocess.run") as mock_run:
            mock_run.return_value = MagicMock(
                returncode=0, stdout="response\n", stderr=""
            )
            response = service.query("test message", conversation_id=existing_id)

            assert response.conversation_id == existing_id
