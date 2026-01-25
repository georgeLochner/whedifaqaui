# Claude Integration Architecture

## Overview

All interactions with Claude in Whedifaqaui are handled through a **backend wrapper module** that programmatically invokes the Claude Code CLI. Users never interact with the CLI directly - they use the web interface exclusively.

## Key Principles

1. **Web UI Only**: Users interact with Claude through the web interface chat panel
2. **Single Integration Point**: All Claude calls go through `services/claude.py`
3. **Conversation Persistence**: UUIDs track conversation state for follow-ups
4. **No Direct CLI Access**: The CLI runs on the server, invoked by backend code

---

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                                USER                                          │
│                                                                              │
│   Opens web app → Types question in chat → Clicks Send                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FRONTEND (React)                                      │
│                                                                              │
│   ChatPanel component                                                        │
│     - Captures user input                                                    │
│     - Displays conversation history                                          │
│     - Shows AI responses with citations                                      │
│     - Stores conversation_id in state                                        │
│                                                                              │
│   POST /api/chat { message, conversation_id? }                              │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        BACKEND API (FastAPI)                                 │
│                                                                              │
│   @router.post("/api/chat")                                                 │
│   async def chat(request: ChatRequest):                                     │
│       # 1. Pre-fetch relevant context from OpenSearch                       │
│       context = await search_service.get_context(request.message)           │
│                                                                              │
│       # 2. Build prompt with context                                        │
│       prompt = build_prompt(request.message, context)                       │
│                                                                              │
│       # 3. Call Claude via wrapper module                                   │
│       response = claude.query(prompt, request.conversation_id)              │
│                                                                              │
│       # 4. Return response with conversation_id                             │
│       return ChatResponse(                                                  │
│           message=response.result,                                          │
│           conversation_id=response.conversation_id,                         │
│           citations=extract_citations(response.result)                      │
│       )                                                                     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CLAUDE WRAPPER MODULE                                     │
│                      (services/claude.py)                                    │
│                                                                              │
│   class ClaudeService:                                                      │
│       def query(message, conversation_id=None) -> ClaudeResponse:           │
│           - If no conversation_id: generate new UUID                        │
│           - If conversation_id: use --resume flag                           │
│           - Invoke CLI via subprocess                                       │
│           - Return {result, conversation_id}                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CLAUDE CODE CLI                                         │
│                                                                              │
│   Installed on server: npm install -g @anthropic-ai/claude-code             │
│                                                                              │
│   Invoked programmatically:                                                 │
│     New conversation:    claude -p "prompt"                                 │
│     Resume conversation: claude --resume <uuid> -p "prompt"                 │
│                                                                              │
│   User NEVER runs this directly                                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Claude Wrapper Module

### Full Implementation

```python
# backend/app/services/claude.py

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
    All user interactions go through: Web UI → API → this module → CLI.

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
```

---

## Use Cases

### 1. Conversational Search (User-Facing)

```python
# backend/app/api/chat.py

from fastapi import APIRouter
from pydantic import BaseModel
from typing import Optional
from app.services.claude import claude
from app.services.search import search_service

router = APIRouter()


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    message: str
    conversation_id: str
    citations: list[dict]


@router.post("/api/chat")
async def chat(request: ChatRequest) -> ChatResponse:
    """
    Handle conversational search from web UI.

    Flow:
    1. User sends message via web UI
    2. Backend fetches relevant context from OpenSearch
    3. Backend calls Claude via wrapper module
    4. Response returned to user with citations
    """
    # 1. Pre-fetch relevant context (Quick Mode)
    context_segments = await search_service.hybrid_search(
        query=request.message,
        limit=10
    )

    # 2. Build prompt with context
    context_text = format_context(context_segments)
    prompt = f"""You are a helpful assistant with access to a video knowledge base.

Context from relevant video segments:
{context_text}

User question: {request.message}

Instructions:
- Answer based on the context provided
- Cite sources using [Video Title @ MM:SS] format
- If the context doesn't contain relevant information, say so
- Be concise but thorough"""

    # 3. Call Claude via wrapper module
    response = claude.query(prompt, request.conversation_id)

    # 4. Extract citations from response
    citations = extract_citations(response.result, context_segments)

    return ChatResponse(
        message=response.result,
        conversation_id=response.conversation_id,
        citations=citations
    )
```

### 2. Entity Extraction (Backend Processing)

```python
# backend/app/tasks/analysis.py

from app.services.claude import claude

def extract_entities_and_relationships(timestamped_transcript: str) -> dict:
    """
    Extract entities from transcript using Claude.

    Note: For processing tasks, we don't need to persist the conversation.
    A new UUID is generated and discarded after the call.
    Uses Haiku model for cost efficiency.
    """
    prompt = f"""Analyze this timestamped transcript and extract:

1. ENTITIES: Named things (people, systems, projects, organizations, concepts)
2. RELATIONSHIPS: How entities relate to each other

Return JSON with this structure:
{{
  "entities": [
    {{
      "name": "entity name",
      "type": "person|system|project|organization|concept",
      "mentions": [
        {{"timestamp": <seconds>, "context": "brief quote"}}
      ]
    }}
  ],
  "relationships": [
    {{
      "source": "entity name",
      "relation": "migrated_from|replaced_by|part_of|works_with",
      "target": "entity name",
      "timestamp": <seconds>
    }}
  ]
}}

Transcript:
{timestamped_transcript}

Return only valid JSON."""

    # Use query_json for structured response, with Haiku for cost efficiency
    result, _ = claude.query_json(prompt, timeout=300, model="haiku")
    return result
```

### 3. LLM-Based Semantic Chunking (Backend Processing)

```python
# backend/app/tasks/chunking.py

from app.services.claude import claude

def chunk_llm_based(whisper_segments: list, config: dict) -> list:
    """
    Use Claude to identify semantic chunk boundaries.
    """
    timestamped_text = build_timestamped_text(whisper_segments)

    prompt = f"""Analyze this timestamped transcript and divide it into semantic chunks.
Each chunk should cover a coherent topic or discussion thread.

Return JSON array:
[
  {{
    "start_time": <seconds>,
    "end_time": <seconds>,
    "summary": "Brief description of what this chunk covers"
  }}
]

Guidelines:
- Create chunks of roughly 1-3 minutes each
- Break at natural topic transitions
- Timestamps are in [MM:SS] format, convert to total seconds

Transcript:
{timestamped_text}

Return only valid JSON array."""

    llm_chunks, _ = claude.query_json(prompt, timeout=300)
    return llm_chunks
```

---

## Conversation Flow

### New Conversation

```
User: "What authentication system do we use?"

Frontend:
  POST /api/chat
  { "message": "What authentication system do we use?" }

Backend:
  1. Search OpenSearch for relevant segments
  2. claude.query(prompt)  # No conversation_id provided
  3. Wrapper generates new UUID: "550e8400-e29b-41d4-a716-446655440000"
     → CLI invoked with: claude --session-id 550e8400... -p "..."

Response:
  {
    "message": "Based on the recordings, you use AWS Cognito...",
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
    "citations": [...]
  }

Frontend stores conversation_id in state
```

### Follow-Up Question

```
User: "When did we migrate to it?"

Frontend:
  POST /api/chat
  {
    "message": "When did we migrate to it?",
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000"
  }

Backend:
  1. Search OpenSearch (may use conversation context to improve query)
  2. claude.query(prompt, conversation_id="550e8400...")
     → CLI invoked with: claude --resume 550e8400... -p "..."
  3. Claude remembers previous context

Response:
  {
    "message": "The migration to Cognito happened in Q2 2024...",
    "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
    "citations": [...]
  }
```

### CLI Flags Summary

| Scenario | CLI Flag | Purpose |
|----------|----------|---------|
| New conversation | `--session-id <uuid>` | Set a specific session ID we can track |
| Resume conversation | `--resume <uuid>` | Continue an existing session |

---

## Configuration

```python
# backend/app/config.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Claude CLI configuration
    claude_cli_path: str = "claude"
    claude_default_timeout: int = 120
    claude_processing_timeout: int = 300  # Longer for entity extraction, etc.

    class Config:
        env_file = ".env"

settings = Settings()
```

```bash
# .env
CLAUDE_CLI_PATH=/usr/local/bin/claude
CLAUDE_DEFAULT_TIMEOUT=120
CLAUDE_PROCESSING_TIMEOUT=300
```

---

## Error Handling

```python
from app.services.claude import claude, ClaudeError

try:
    response = claude.query(prompt, conversation_id)
except ClaudeError as e:
    # CLI returned non-zero exit code
    logger.error(f"Claude error: {e}")
    raise HTTPException(500, "AI service temporarily unavailable")
except subprocess.TimeoutExpired:
    # Request took too long
    logger.error("Claude request timed out")
    raise HTTPException(504, "AI response timed out")
```

---

## Summary

| Component | Role |
|-----------|------|
| **Web UI** | User's only interface - chat panel for questions |
| **FastAPI Backend** | Receives requests, fetches context, calls Claude module |
| **Claude Wrapper Module** | Single integration point for all Claude interactions |
| **Claude Code CLI** | Runs on server, invoked programmatically, never by user |
| **Conversation ID** | UUID that enables follow-up questions and context retention |
