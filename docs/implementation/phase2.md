# Phase 2: High-Level Architectural Plan

**Phase**: Conversational AI (Quick Mode)
**Goal**: Transform basic search into an AI-powered conversational experience with pre-fetched context and a dynamic results workspace.

---

## Phase 2 Scope

| Story | Description |
|-------|-------------|
| S7 | Conversational Search - Chat-style AI interaction with context memory |
| S8 | Results List - Scrollable list of accumulated findings |
| S9 | Content Pane - Click-to-view in dedicated content area |
| S2 | AI Summaries - Synthesized answers citing multiple sources |
| S10 | Document Generation - Generate and download summary documents |
| V4 | Recording Date - Date field for temporal relevance |

---

## Key Architectural Addition: Claude Wrapper Module

**Critical**: This phase introduces `services/claude.py` - the single integration point for all Claude interactions.

```
User → Web UI → FastAPI → services/claude.py → Claude Code CLI
                                    ↓
                          subprocess.run(["claude", "-p", prompt], cwd=PROJECT_ROOT)
```

- **No `anthropic` library** - CLI only via subprocess
- **Conversation persistence** via `--session-id` and `--resume` flags
- **All Claude calls** go through this module (never bypass)
- **File references** - pass file paths for large content, not text in prompt
- **Working directory** - set to project root so Claude can access data files
- **Output format** - pipe-delimited for structured data (not JSON), markdown for user responses

---

## Architecture: Quick Mode Query Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  USER: "What authentication system do we use?"                               │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  FRONTEND: ChatPanel                                                         │
│                                                                              │
│  POST /api/chat { message: "...", conversation_id: null }                   │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  BACKEND: Chat Route                                                         │
│                                                                              │
│  1. Hybrid search OpenSearch (BM25 + vector)                                │
│  2. Retrieve top 10-20 relevant segments                                    │
│  3. Write context to temp file: /data/temp/context_{uuid}.json              │
│  4. Build prompt with FILE REFERENCE (not inline text)                      │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CLAUDE WRAPPER: services/claude.py                                          │
│                                                                              │
│  claude.query(prompt, conversation_id=None)                                 │
│    → Generates new UUID                                                     │
│    → subprocess.run(                                                        │
│        ["claude", "--session-id", uuid, "-p", prompt],                      │
│        cwd=PROJECT_ROOT  # So Claude can access /data files                 │
│      )                                                                      │
│    → Returns ClaudeResponse(result, conversation_id)                        │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  RESPONSE                                                                    │
│                                                                              │
│  {                                                                          │
│    "message": "Based on the recordings, you use AWS Cognito...",           │
│    "conversation_id": "550e8400-e29b-41d4-a716-446655440000",              │
│    "citations": [                                                           │
│      { "video_id": "...", "title": "Auth Meeting", "timestamp": 125.5 }    │
│    ]                                                                        │
│  }                                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Project Structure Changes (Phase 2 Additions)

```
backend/
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── chat.py             # NEW: S7, S2 - Conversational endpoint
│   │       └── documents.py        # NEW: S10 - Document generation
│   │
│   ├── services/
│   │   ├── claude.py               # NEW: Claude wrapper module (critical)
│   │   ├── chat.py                 # NEW: Chat orchestration logic
│   │   ├── document.py             # NEW: Document generation
│   │   └── prompt.py               # NEW: Prompt building utilities
│   │
│   ├── models/
│   │   ├── video.py                # MODIFIED: Add recording_date (V4)
│   │   └── document.py             # NEW: Generated documents model
│   │
│   └── schemas/
│       ├── chat.py                 # NEW: Chat request/response schemas
│       └── document.py             # NEW: Document schemas

frontend/
├── src/
│   ├── pages/
│   │   └── WorkspacePage.tsx       # NEW: Three-panel workspace (replaces SearchPage)
│   │
│   ├── components/
│   │   ├── workspace/              # NEW: Workspace components
│   │   │   ├── ConversationPanel.tsx   # S7: Chat interface
│   │   │   ├── ResultsPanel.tsx        # S8: Accumulated results list
│   │   │   └── ContentPane.tsx         # S9: Video/document viewer
│   │   │
│   │   ├── chat/                   # NEW: Chat components
│   │   │   ├── ChatInput.tsx       # Message input
│   │   │   ├── ChatMessage.tsx     # Single message display
│   │   │   ├── ChatHistory.tsx     # Message list
│   │   │   └── Citation.tsx        # Clickable citation
│   │   │
│   │   └── documents/              # NEW: Document components
│   │       ├── DocumentCard.tsx    # S10: Document in results
│   │       └── DocumentViewer.tsx  # S9: Document display
│   │
│   ├── api/
│   │   ├── chat.ts                 # NEW: Chat API client
│   │   └── documents.ts            # NEW: Documents API client
│   │
│   ├── hooks/
│   │   ├── useChat.ts              # NEW: Chat state management
│   │   └── useWorkspace.ts         # NEW: Workspace state (results, content)
│   │
│   └── types/
│       ├── chat.ts                 # NEW: Chat types
│       └── document.ts             # NEW: Document types
```

---

## Component Specification by Layer

### Backend: Claude Wrapper Module (`services/claude.py`)

**This is the most critical component of Phase 2.**

| Method | Purpose |
|--------|---------|
| `query(message, conversation_id?, timeout?, model?)` | Send message, get response |
| `query_json(message, conversation_id?, timeout?, model?)` | Send message, parse JSON response |

```python
@dataclass
class ClaudeResponse:
    result: str
    conversation_id: str

class ClaudeService:
    def query(self, message: str, conversation_id: str = None) -> ClaudeResponse:
        # If no conversation_id → generate UUID, use --session-id
        # If conversation_id → use --resume
        ...

claude = ClaudeService()  # Singleton
```

### Backend: New API Routes

| Route | Method | Purpose | Stories |
|-------|--------|---------|---------|
| `/api/chat` | POST | Send message, get AI response | S7, S2 |
| `/api/documents` | POST | Generate summary document | S10 |
| `/api/documents/{id}` | GET | Retrieve generated document | S10 |
| `/api/documents/{id}/download` | GET | Download as file | S10 |

### Backend: New Services

| Service | Responsibility |
|---------|----------------|
| `claude.py` | Claude CLI wrapper (subprocess invocation) |
| `chat.py` | Chat orchestration (search → context → Claude → response) |
| `document.py` | Document generation and storage |
| `prompt.py` | Prompt template building with context |

### Backend: New/Modified Models

| Model | Change | Fields |
|-------|--------|--------|
| `Video` | MODIFIED | Add `recording_date` (DATE, required) - V4 |
| `GeneratedDocument` | NEW | id, session_id, title, content, source_segment_ids[], created_at |

### Frontend: Three-Panel Layout

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Navigation Bar                                                              │
├───────────────────────┬─────────────────────┬───────────────────────────────┤
│                       │                     │                               │
│  CONVERSATION PANEL   │   RESULTS PANEL     │      CONTENT PANE             │
│  (S7)                 │   (S8)              │      (S9)                     │
│                       │                     │                               │
│  ┌─────────────────┐  │  ┌───────────────┐  │  ┌───────────────────────┐   │
│  │ AI: Based on... │  │  │ Video: Auth   │  │  │                       │   │
│  │ [Auth @ 2:05]   │  │  │ Meeting       │  │  │    Video Player       │   │
│  └─────────────────┘  │  │ @ 2:05        │  │  │    or                 │   │
│                       │  ├───────────────┤  │  │    Document Viewer    │   │
│  ┌─────────────────┐  │  │ Video: Tech   │  │  │                       │   │
│  │ User: When did  │  │  │ Review        │  │  │                       │   │
│  │ we migrate?     │  │  │ @ 15:30       │  │  └───────────────────────┘   │
│  └─────────────────┘  │  ├───────────────┤  │                               │
│                       │  │ Document:     │  │  ┌───────────────────────┐   │
│  ┌─────────────────┐  │  │ Summary.md    │  │  │   Transcript Panel    │   │
│  │ AI: The migra...│  │  └───────────────┘  │  │   (synchronized)      │   │
│  └─────────────────┘  │                     │  └───────────────────────┘   │
│                       │                     │                               │
│  ┌─────────────────┐  │                     │                               │
│  │ Type message... │  │                     │                               │
│  └─────────────────┘  │                     │                               │
│                       │                     │                               │
├───────────────────────┴─────────────────────┴───────────────────────────────┤
│  ~30%                   ~25%                  ~45%                           │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Frontend: New Pages

| Page | Route | Stories | Description |
|------|-------|---------|-------------|
| `WorkspacePage` | `/workspace` | S7, S8, S9, S10 | Three-panel conversational interface |

### Frontend: New Component Groups

| Group | Components | Purpose |
|-------|------------|---------|
| `workspace/` | ConversationPanel, ResultsPanel, ContentPane | Three-panel layout |
| `chat/` | ChatInput, ChatMessage, ChatHistory, Citation | Chat UI elements |
| `documents/` | DocumentCard, DocumentViewer | Document display |

### Frontend: New Hooks

| Hook | State Managed |
|------|---------------|
| `useChat` | messages[], conversationId, isLoading, sendMessage() |
| `useWorkspace` | results[], selectedResult, addResult(), selectResult() |

---

## Data Flow: Conversational Search

### New Conversation

```
1. User types: "What authentication system do we use?"
2. Frontend: POST /api/chat { message: "...", conversation_id: null }
3. Backend:
   a. Hybrid search OpenSearch → top 10 segments
   b. Build prompt with context
   c. claude.query(prompt) → generates new UUID
   d. CLI: claude --session-id <uuid> -p "..."
4. Response: { message, conversation_id, citations }
5. Frontend:
   a. Display message in ConversationPanel
   b. Add citations to ResultsPanel
   c. Store conversation_id in state
```

### Follow-Up Question

```
1. User types: "When did we migrate to it?"
2. Frontend: POST /api/chat { message: "...", conversation_id: "<stored-uuid>" }
3. Backend:
   a. Search (may enhance query with conversation context)
   b. Build prompt with new context
   c. claude.query(prompt, conversation_id) → uses existing UUID
   d. CLI: claude --resume <uuid> -p "..."
4. Response: { message, conversation_id, citations }
5. Frontend: Append to conversation, add new citations to results
```

### Document Generation

```
1. User: "Summarize the second video"
2. Frontend: POST /api/documents { request: "summarize", source_ids: [...] }
3. Backend:
   a. Fetch full transcript(s)
   b. claude.query(summary_prompt)
   c. Save GeneratedDocument to database
4. Response: { document_id, title, preview }
5. Frontend: Add document to ResultsPanel
6. User clicks document → ContentPane shows full document
7. User clicks Download → GET /api/documents/{id}/download
```

---

## Database Changes

### Modified: videos table

```sql
-- V4: Recording date is now required and used for temporal queries
ALTER TABLE videos
  ALTER COLUMN recording_date SET NOT NULL;

-- Add index for date-based queries
CREATE INDEX idx_videos_recording_date ON videos(recording_date);
```

### New: generated_documents table

```sql
CREATE TABLE generated_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(100),  -- Browser session or user session
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,  -- Markdown content
    source_segment_ids UUID[],  -- Segments used to generate
    source_video_ids UUID[],    -- Videos referenced
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_documents_session ON generated_documents(session_id);
```

---

## API Contracts

### POST /api/chat

**Request:**
```json
{
  "message": "What authentication system do we use?",
  "conversation_id": null
}
```

**Response:**
```json
{
  "message": "Based on the recordings, you use AWS Cognito for authentication. In the Auth Meeting from March 2024, John explained that the team migrated from Auth0 to Cognito...",
  "conversation_id": "550e8400-e29b-41d4-a716-446655440000",
  "citations": [
    {
      "video_id": "abc123",
      "video_title": "Auth Meeting",
      "timestamp": 125.5,
      "text": "We decided to migrate to Cognito because..."
    }
  ]
}
```

### POST /api/documents

**Request:**
```json
{
  "request": "Summarize the authentication discussion",
  "source_video_ids": ["abc123", "def456"],
  "format": "markdown"
}
```

**Response:**
```json
{
  "id": "doc-789",
  "title": "Authentication Discussion Summary",
  "preview": "This document summarizes the authentication system...",
  "source_count": 2,
  "created_at": "2024-03-15T10:30:00Z"
}
```

---

## Claude Output Format Strategy

### Why Not JSON?

Claude does not reliably produce valid JSON:
- Trailing commas, comments, unquoted keys
- Preamble text before JSON
- Truncation on long outputs
- Markdown code block wrapping

### Output Format by Task Type

| Task | Output Format | Reason |
|------|---------------|--------|
| User chat response | Markdown (stdout) | Natural for display |
| Structured extraction | Pipe-delimited (file) | Reliable parsing |
| Document generation | Markdown (file) | Natural for documents |

### Pipe-Delimited Format

Simple, reliable, easy to parse:

```
TYPE|FIELD1|FIELD2|FIELD3
ENTITY|AWS Cognito|system|Authentication service
REL|Cognito|replaced|Auth0|125
SPEAKER|SPEAKER_00|John Smith|0.9
```

**Rules:**
- One record per line
- Fields separated by `|`
- First field = record type
- Lines starting with `#` = comments (ignored)
- Empty fields allowed: `TYPE|value||value`

### Parser Implementation

```python
# services/output_parser.py

def parse_pipe_delimited(text: str) -> dict:
    """Parse Claude's pipe-delimited output."""
    result = {
        "entities": [],
        "relationships": [],
        "speakers": {},
        "frames": [],
        "topics": []
    }

    for line in text.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        parts = line.split('|')
        record_type = parts[0]

        if record_type == 'ENTITY':
            result["entities"].append({
                "name": parts[1],
                "type": parts[2],
                "description": parts[3] if len(parts) > 3 else ""
            })
        elif record_type == 'REL':
            result["relationships"].append({
                "source": parts[1],
                "relation": parts[2],
                "target": parts[3],
                "timestamp": float(parts[4]) if len(parts) > 4 and parts[4] else None
            })
        elif record_type == 'SPEAKER':
            result["speakers"][parts[1]] = {
                "name": parts[2],
                "confidence": float(parts[3]) if len(parts) > 3 else 1.0
            }
        elif record_type == 'FRAME':
            result["frames"].append({
                "timestamp": float(parts[1]),
                "reason": parts[2] if len(parts) > 2 else ""
            })
        elif record_type == 'TOPIC':
            result["topics"].append(parts[1])

    return result
```

---

## Prompt Templates

### Quick Mode Context Prompt

```python
QUICK_MODE_PROMPT = """You are a helpful assistant with access to a video knowledge base.

READ THE CONTEXT FILE: {context_file_path}

The file contains relevant video segments in JSON format with:
- video_id, video_title
- timestamp (seconds)
- text content
- speaker (if available)

User question: {question}

Instructions:
- Read the context file first
- Answer based ONLY on the context provided
- Cite sources using [Video Title @ MM:SS] format
- If the context doesn't contain relevant information, say so clearly
- Be concise but thorough
- You can reference previous messages in our conversation"""
```

### Document Generation Prompt

```python
DOCUMENT_PROMPT = """Generate a summary document based on video transcript content.

READ THE SOURCE FILE: {source_file_path}

The file contains transcript segments to summarize.

User Request: {request}

Instructions:
- Read the source file first
- Create a well-structured markdown document
- Include a title and sections as appropriate
- Cite timestamps for key points using [MM:SS] format
- Be comprehensive but avoid unnecessary repetition"""
```

### File Format for Context

```json
// /data/temp/context_{uuid}.json
{
  "query": "What authentication system do we use?",
  "segments": [
    {
      "video_id": "vid-123",
      "video_title": "Auth Migration Meeting",
      "timestamp": 125.5,
      "text": "We decided to migrate from Auth0 to Cognito...",
      "speaker": "SPEAKER_00"
    }
  ]
}
```

---

## File Management for Claude Interactions

### Why File References?

| Approach | Problem |
|----------|---------|
| Text in prompt | OS command-line limits (~128KB-2MB), unwieldy prompts |
| File reference | Claude reads file directly, clean separation of data/instructions |

### Temp Files for Context

```python
# services/chat.py

import json
import uuid
from pathlib import Path

TEMP_DIR = Path("/data/temp")

def prepare_context_file(segments: list, query: str) -> str:
    """Write context to temp file, return path for Claude."""
    file_id = str(uuid.uuid4())
    file_path = TEMP_DIR / f"context_{file_id}.json"

    context = {
        "query": query,
        "segments": [
            {
                "video_id": str(seg.video_id),
                "video_title": seg.video_title,
                "timestamp": seg.start_time,
                "text": seg.text,
                "speaker": seg.speaker
            }
            for seg in segments
        ]
    }

    with open(file_path, "w") as f:
        json.dump(context, f, indent=2)

    return str(file_path)

def cleanup_context_file(file_path: str):
    """Remove temp file after Claude response."""
    Path(file_path).unlink(missing_ok=True)
```

### Temp File Lifecycle

```
1. User sends query
2. Backend searches OpenSearch → segments
3. Backend writes segments to /data/temp/context_{uuid}.json
4. Backend sends prompt with file path to Claude
5. Claude reads file, generates response
6. Backend deletes temp file
7. Response returned to user
```

### Cleanup Strategy

- Delete temp files immediately after Claude response
- Periodic cleanup job for orphaned files (older than 1 hour)
- Temp directory excluded from backups

---

## Session Management

### Conversation State

| Component | Stored Where | Purpose |
|-----------|--------------|---------|
| `conversation_id` | Frontend state (React) | Track Claude conversation |
| `results[]` | Frontend state (React) | Accumulated findings |
| `session_id` | Cookie/localStorage | Link generated documents |

### Lifecycle

```
1. User opens /workspace → new session begins
2. First message → new conversation_id generated
3. Follow-ups → same conversation_id (Claude remembers context)
4. Close browser → session ends (no persistence in Phase 2)
5. Phase 7 adds conversation persistence
```

---

## What's Deferred

| Component | Phase |
|-----------|-------|
| Entity search/filtering | Phase 3 |
| Speaker attribution | Phase 3 |
| Deep Mode (REST API tools) | Phase 4 |
| Conversation persistence | Phase 7 |

---

## Success Criteria

- [ ] User can have multi-turn conversation with AI
- [ ] AI references previous context ("the second video")
- [ ] Results accumulate in scrollable list
- [ ] Clicking result shows content in ContentPane
- [ ] Summary documents can be generated and downloaded
- [ ] Response time: ~10-20 seconds
