import subprocess
import uuid
import json
import logging
from dataclasses import dataclass
from typing import Optional

logger = logging.getLogger(__name__)


class ClaudeError(Exception):
    """Raised when Claude CLI returns an error."""
    pass


@dataclass
class ClaudeResponse:
    """Response from Claude wrapper."""
    result: str
    conversation_id: str


class ClaudeService:
    """
    Wrapper module for all Claude Code CLI interactions.

    This is the ONLY way the system communicates with Claude.
    All user interactions go through: Web UI -> API -> this module -> CLI.

    Usage:
        from app.services.claude import claude

        # New conversation
        response = claude.query("What is the auth system?")
        print(response.result)
        print(response.conversation_id)  # Save this for follow-ups

        # Continue conversation
        response = claude.query(
            "Tell me more about the migration",
            conversation_id=saved_id
        )
    """

    def __init__(self, cli_path: str = "claude"):
        """
        Initialize Claude service.

        Args:
            cli_path: Path to Claude CLI executable (default: "claude")
        """
        self.cli_path = cli_path
        self.default_model = None  # Use CLI default unless specified

    def query(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        timeout: int = 120,
        model: Optional[str] = None
    ) -> ClaudeResponse:
        """
        Send a query to Claude and get a response.

        Args:
            message: The message/prompt to send to Claude
            conversation_id: Optional UUID to resume an existing conversation.
                           If not provided, creates a new conversation.
            timeout: Maximum time to wait for response (seconds)
            model: Optional model to use (e.g., "haiku" for cost-efficient tasks).
                   If not provided, uses CLI default.

        Returns:
            ClaudeResponse with:
                - result: The text response from Claude
                - conversation_id: UUID for this conversation (new or existing)

        Raises:
            ClaudeError: If CLI returns non-zero exit code
            subprocess.TimeoutExpired: If timeout exceeded
        """
        # Generate new conversation ID if not resuming
        is_new_conversation = conversation_id is None
        if is_new_conversation:
            conversation_id = str(uuid.uuid4())

        # Build command
        cmd = [self.cli_path]
        if model:
            cmd.extend(["--model", model])
        if is_new_conversation:
            # Set session ID for new conversation so we can track it
            cmd.extend(["--session-id", conversation_id])
        else:
            # Resume existing conversation
            cmd.extend(["--resume", conversation_id])
        cmd.extend(["-p", message])

        logger.info(
            f"Invoking Claude CLI: new={is_new_conversation}, "
            f"conv_id={conversation_id[:8]}..."
        )

        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=timeout
            )
        except subprocess.TimeoutExpired:
            logger.error(f"Claude CLI timed out after {timeout}s")
            raise

        if result.returncode != 0:
            logger.error(f"Claude CLI error: {result.stderr}")
            raise ClaudeError(f"CLI error (code {result.returncode}): {result.stderr}")

        logger.info(f"Claude response received: {len(result.stdout)} chars")

        return ClaudeResponse(
            result=result.stdout.strip(),
            conversation_id=conversation_id
        )

    def query_json(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        timeout: int = 300,
        model: Optional[str] = None
    ) -> tuple[dict, str]:
        """
        Send a query expecting JSON response.

        Useful for structured outputs like entity extraction.

        Args:
            message: Prompt that instructs Claude to return JSON
            conversation_id: Optional UUID to resume conversation
            timeout: Maximum wait time (default longer for structured tasks)
            model: Optional model to use (e.g., "haiku" for cost-efficient tasks)

        Returns:
            Tuple of (parsed_json_dict, conversation_id)

        Raises:
            json.JSONDecodeError: If response is not valid JSON
        """
        response = self.query(message, conversation_id, timeout, model)

        # Try to extract JSON from response
        text = response.result

        # Handle case where JSON is wrapped in markdown code blocks
        if "```json" in text:
            start = text.find("```json") + 7
            end = text.find("```", start)
            text = text[start:end].strip()
        elif "```" in text:
            start = text.find("```") + 3
            end = text.find("```", start)
            text = text[start:end].strip()

        parsed = json.loads(text)
        return parsed, response.conversation_id


# Singleton instance used throughout the application
claude = ClaudeService()
