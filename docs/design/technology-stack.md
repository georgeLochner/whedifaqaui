# Technology Stack

## Overview

This document details all technologies, libraries, and frameworks used in Whedifaqaui, organized by implementation phase with pinned versions for reproducibility.

**Last Updated**: January 2025

---

## ⚠️ Version Freeze Policy

**All versions in this document are FROZEN** for the duration of active development.

**DO NOT:**
- Update Docker image versions (postgres, opensearch, redis, neo4j)
- Update major/minor versions of Python/Node packages
- Use floating tags (`:latest`, `:16-alpine` instead of `:16.1-alpine`)

**WHY:**
- Prevents large image re-downloads across team (OpenSearch = 826MB)
- Ensures reproducibility across all environments
- Avoids mid-development breaking changes
- Maintains consistency between dev, test, and production

**TO UPDATE A VERSION:**
1. Create a dedicated task for version upgrade evaluation
2. Test thoroughly across all phases
3. Update this document + docker-compose.yml + Dockerfiles simultaneously
4. Document breaking changes and migration steps

**Current frozen versions effective as of**: January 2025

---

## Version Summary

| Category | Technology | Version | Phase Introduced |
|----------|------------|---------|------------------|
| **Runtime** | Python | 3.11 | 1 |
| **Runtime** | Node.js | 20.x LTS | 1 |
| **Frontend** | React | 18.2.x | 1 |
| **Frontend** | Vite | 5.4.x | 1 |
| **Frontend** | Tailwind CSS | 3.4.x | 1 |
| **Frontend** | Video.js | 8.6.x | 1 |
| **Backend** | FastAPI | 0.109.x | 1 |
| **Backend** | Celery | 5.3.x | 1 |
| **Database** | PostgreSQL | 16 | 1 |
| **Search** | OpenSearch | 2.11.x | 1 |
| **Cache** | Redis | 7.2.x | 1 |
| **AI/ML** | WhisperX | 3.1.x | 1 |
| **AI/ML** | pyannote.audio | 3.1.x | 1 |
| **AI/ML** | sentence-transformers | 2.6.x | 1 |
| **AI/ML** | Claude Code CLI | Latest | 2 |
| **Graph DB** | Neo4j | 5.15.x | 5 |

---

## Docker Images (All Phases)

**⚠️ THESE VERSIONS ARE FROZEN - Do not change without explicit task**

| Service | Version | Docker Image | Phase |
|---------|---------|--------------|-------|
| PostgreSQL | **16.1** | `postgres:16.1-alpine` | 1 |
| OpenSearch | **2.11.1** | `opensearchproject/opensearch:2.11.1` | 1 |
| Redis | **7.2.4** | `redis:7.2.4-alpine` | 1 |
| Neo4j | **5.15.0** | `neo4j:5.15.0-community` | 5 |

**Base Images for Application Containers:**

| Container | Base Image | Version |
|-----------|------------|---------|
| Backend | `python:3.11-slim` | 3.11 |
| Worker | `python:3.11-slim` | 3.11 |
| Worker-GPU | `nvidia/cuda:12.1.0-runtime-ubuntu22.04` | CUDA 12.1 |
| Frontend | `node:20-alpine` | Node 20 LTS |

**Why these specific versions:**
- **Patch version pinning** (16.1, not 16.x) prevents unexpected minor updates
- **Alpine variants** reduce image size where available
- **LTS versions** for Node.js (20.x) and Python (3.11)
- **Specific CUDA version** for GPU worker reproducibility

**To verify versions in use:**
```bash
docker compose config | grep "image:"
```

---

## Phase 1: MVP Core

**Goal**: Upload → Transcribe → Basic Search → Play at Timestamp

### Frontend Stack

| Package | Version | Purpose |
|---------|---------|---------|
| react | 18.2.x | UI framework |
| react-dom | 18.2.x | React DOM renderer |
| typescript | 5.3.x | Type-safe JavaScript |
| vite | 5.4.x | Build tool and dev server |
| tailwindcss | 3.4.x | Utility-first CSS |
| video.js | 8.6.x | HTML5 video player |
| axios | 1.6.x | HTTP client |
| react-router-dom | 6.22.x | Client-side routing |

```json
{
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.22.0",
    "axios": "^1.6.7",
    "video.js": "^8.6.1"
  },
  "devDependencies": {
    "typescript": "^5.3.3",
    "vite": "^5.4.0",
    "tailwindcss": "^3.4.1",
    "@types/react": "^18.2.48",
    "@types/react-dom": "^18.2.18",
    "@vitejs/plugin-react": "^4.2.1"
  }
}
```

### Backend Stack

| Package | Version | Purpose |
|---------|---------|---------|
| fastapi | 0.109.x | Async REST API framework |
| uvicorn | 0.27.x | ASGI server |
| celery | 5.3.x | Distributed task queue |
| redis | 5.0.x | Celery broker client |
| sqlalchemy | 2.0.x | ORM |
| alembic | 1.13.x | Database migrations |
| psycopg2-binary | 2.9.x | PostgreSQL driver |
| opensearch-py | 2.4.x | OpenSearch client |
| ffmpeg-python | 0.2.0 | Video processing |
| whisperx | 3.1.x | Transcription + speaker diarization |
| pyannote.audio | 3.1.x | Speaker diarization models (used by WhisperX) |
| sentence-transformers | 2.6.x | Embeddings |
| pydantic | 2.6.x | Data validation |
| python-multipart | 0.0.6 | File uploads |
| python-dotenv | 1.0.x | Environment variables |

```txt
# requirements-phase1.txt

# Web Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6
pydantic==2.6.1
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.25
psycopg2-binary==2.9.9
alembic==1.13.1

# Search
opensearch-py==2.4.2

# Task Queue
celery==5.3.6
redis==5.0.1

# Video Processing
ffmpeg-python==0.2.0

# Transcription + Speaker Diarization
# WhisperX provides transcription (via faster-whisper) AND speaker diarization (via pyannote)
whisperx>=3.1.0
pyannote.audio>=3.1.0
# Note: Requires HuggingFace token for pyannote models
# Note: Requires CUDA 11 or 12 depending on ctranslate2 version

# Embeddings
sentence-transformers==2.6.1
torch==2.1.2  # Or torch with CUDA support

# Utilities
python-dotenv==1.0.0
```

### Infrastructure

| Service | Version | Docker Image |
|---------|---------|--------------|
| PostgreSQL | 16.1 | `postgres:16.1-alpine` |
| OpenSearch | 2.11.1 | `opensearchproject/opensearch:2.11.1` |
| Redis | 7.2.4 | `redis:7.2.4-alpine` |

### FFmpeg

| Tool | Version | Notes |
|------|---------|-------|
| FFmpeg | 6.x or 7.x | System package or Docker |

```dockerfile
# For Ubuntu/Debian
RUN apt-get update && apt-get install -y ffmpeg
```

---

## Phase 2: Conversational AI (Quick Mode)

**Goal**: Claude CLI integration, three-panel UI, session-based conversations

### Additional Frontend Packages

| Package | Version | Purpose |
|---------|---------|---------|
| @tanstack/react-query | 5.17.x | Server state management |
| react-markdown | 9.0.x | Markdown rendering |
| remark-gfm | 4.0.x | GitHub Flavored Markdown |

```json
{
  "dependencies": {
    "@tanstack/react-query": "^5.17.0",
    "react-markdown": "^9.0.1",
    "remark-gfm": "^4.0.0"
  }
}
```

### Claude Integration

**IMPORTANT**: Users interact with Claude exclusively through the web interface. They never invoke the Claude Code CLI directly. All Claude interactions are handled by a backend wrapper module.

| Tool | Version | Notes |
|------|---------|-------|
| Claude Code CLI | Latest | Installed on server via `npm install -g @anthropic-ai/claude-code` |

#### Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              WEB BROWSER                                     │
│                                                                              │
│   User types question in chat interface → clicks Send                       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ HTTP POST /api/chat
┌─────────────────────────────────────────────────────────────────────────────┐
│                           FASTAPI BACKEND                                    │
│                                                                              │
│   Chat endpoint receives message + optional conversation_id                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ claude.query(message, conversation_id)
┌─────────────────────────────────────────────────────────────────────────────┐
│                      CLAUDE WRAPPER MODULE                                   │
│                         (services/claude.py)                                 │
│                                                                              │
│   - Manages conversation state via UUIDs                                    │
│   - Invokes Claude Code CLI via subprocess                                  │
│   - Handles all LLM interactions for the entire system                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼ subprocess.run(["claude", ...])
┌─────────────────────────────────────────────────────────────────────────────┐
│                         CLAUDE CODE CLI                                      │
│                                                                              │
│   Runs on server, invoked programmatically                                  │
│   User never sees or touches this directly                                  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Claude Wrapper Module Interface

```python
# services/claude.py

import subprocess
import uuid
import json
from dataclasses import dataclass
from typing import Optional

@dataclass
class ClaudeResponse:
    """Response from Claude wrapper."""
    result: str
    conversation_id: str

class ClaudeService:
    """
    Wrapper module for all Claude Code CLI interactions.

    This is the ONLY way the system communicates with Claude.
    Users interact via web UI → backend API → this module → CLI.
    """

    def query(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        timeout: int = 120
    ) -> ClaudeResponse:
        """
        Send a query to Claude and get a response.

        Args:
            message: The message/prompt to send to Claude
            conversation_id: Optional UUID to resume an existing conversation.
                           If not provided, creates a new conversation.
            timeout: Maximum time to wait for response (seconds)

        Returns:
            ClaudeResponse with result text and conversation_id

        Usage:
            # New conversation
            response = claude.query("What is the auth system?")
            # response.conversation_id = "550e8400-e29b-..."

            # Continue conversation
            response = claude.query(
                "Tell me more about the migration",
                conversation_id="550e8400-e29b-..."
            )
        """
        # Generate new conversation ID if not resuming
        is_new_conversation = conversation_id is None
        if is_new_conversation:
            conversation_id = str(uuid.uuid4())

        # Build command
        if is_new_conversation:
            # Set session ID for new conversation so we can track it
            cmd = ["claude", "--session-id", conversation_id, "-p", message]
        else:
            # Resume existing conversation
            cmd = ["claude", "--resume", conversation_id, "-p", message]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout
        )

        if result.returncode != 0:
            raise ClaudeError(f"CLI error: {result.stderr}")

        return ClaudeResponse(
            result=result.stdout,
            conversation_id=conversation_id
        )

# Singleton instance used throughout the application
claude = ClaudeService()
```

#### All Claude Use Cases

The wrapper module is used for ALL Claude interactions:

| Use Case | Called By | Example |
|----------|-----------|---------|
| Conversational search | Chat API endpoint | `claude.query(user_message, conv_id)` |
| Entity extraction | Processing pipeline (Celery) | `claude.query(extraction_prompt, model="haiku")` |
| LLM-based chunking | Processing pipeline (Celery) | `claude.query(chunking_prompt, model="haiku")` |
| Segment summaries | Processing pipeline (Celery) | `claude.query(summary_prompt, model="haiku")` |

**Note**: Processing tasks use `model="haiku"` for cost efficiency. Conversational search uses the default model for higher quality responses.

For one-off processing tasks (entity extraction, chunking), we don't need to persist the conversation - a new UUID is generated and discarded. For user-facing chat, we persist the conversation_id to enable follow-up questions.

---

## Phase 3: Intelligent Analysis

**Goal**: Entity extraction, speaker name mapping, visual content analysis

**Clarification**: Speaker *diarization* (labeling segments as SPEAKER_00, SPEAKER_01) is provided by WhisperX in Phase 1. Phase 3 adds speaker *name mapping* where Claude infers actual names from context ("SPEAKER_00" → "John Smith").

### Additional Backend Packages

| Package | Version | Purpose |
|---------|---------|---------|
| opencv-python | 4.9.x | Frame extraction |
| pillow | 10.2.x | Image processing |

**Note**: No OCR library needed - Claude reads image files directly and extracts visible text.

```txt
# requirements-phase3.txt (additions)

# Visual Content Analysis
opencv-python==4.9.0.80
pillow==10.2.0

# Note: No pytesseract/tesseract needed - Claude handles text extraction from images
```

### System Dependencies

```dockerfile
# Phase 3 system dependencies
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx  # For OpenCV
```

### What Phase 3 Adds (Not Diarization)

| Feature | Description |
|---------|-------------|
| Speaker name mapping | Claude infers names from transcript context |
| Speaker mapping UI | Users can correct Claude's inferences |
| Entity extraction | People, systems, projects extracted from transcripts |
| Visual frame analysis | Claude describes critical frames and extracts text |

---

## Phase 4: Agentic Search (Deep Mode)

**Goal**: REST API endpoints for iterative retrieval via Claude

### Architecture

In Deep Mode, Claude can iteratively query the knowledge base by requesting API calls. The system:

1. Provides Claude with a **context prompt** documenting available API endpoints
2. Claude includes `curl` commands in its responses when it needs data
3. Backend **parses and executes** these API calls
4. Results are **fed back to Claude** for further processing
5. Loop continues until Claude has enough information to answer

```
User Question
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│  Claude receives question + API documentation                    │
│                                                                  │
│  "You have access to these endpoints:                           │
│   - GET /api/search?query=...                                   │
│   - GET /api/entities/{name}                                    │
│   - GET /api/videos/{id}/transcript                             │
│   To use them, output: CALL: curl <endpoint>"                   │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼
┌─────────────────────────────────────────────────────────────────┐
│  Claude Response (may include API calls)                         │
│                                                                  │
│  "To answer this, I need to search for authentication info.     │
│   CALL: curl http://localhost:8000/api/search?query=auth"       │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼ Backend detects CALL:, executes request
┌─────────────────────────────────────────────────────────────────┐
│  API Response fed back to Claude                                 │
│                                                                  │
│  "API Response: [{segment: ..., video: ..., timestamp: ...}]"   │
└─────────────────────────────────────────────────────────────────┘
     │
     ▼ Loop until Claude provides final answer
┌─────────────────────────────────────────────────────────────────┐
│  Final Answer with citations                                     │
└─────────────────────────────────────────────────────────────────┘
```

### No Additional Packages Required

Phase 4 uses existing FastAPI endpoints - no new dependencies.

```txt
# requirements-phase4.txt (additions)

# No additional packages - uses existing FastAPI REST endpoints
# Claude accesses the API via curl commands parsed by the backend
```

### Search API Endpoints

See `docs/architecture/search-api.md` for complete API documentation.

| Endpoint | Purpose |
|----------|---------|
| `GET /api/search` | Hybrid semantic + keyword search |
| `GET /api/search/speaker/{name}` | Search by speaker |
| `GET /api/search/date-range` | Search by recording date |
| `GET /api/entities/{name}` | Get entity details + relationships |
| `GET /api/videos/{id}/transcript` | Get full transcript |
| `GET /api/segments/{id}/context` | Expand context around a segment |
| `GET /api/videos` | List all videos |
| `GET /api/topics/{name}/timeline` | Chronological topic view |

---

## Phase 5: Knowledge Graph

**Goal**: Neo4j integration and graph visualization

### Additional Infrastructure

| Service | Version | Docker Image |
|---------|---------|--------------|
| Neo4j | 5.15.0 | `neo4j:5.15.0-community` |

### Additional Backend Packages

| Package | Version | Purpose |
|---------|---------|---------|
| neo4j | 5.15.x | Neo4j Python driver |

```txt
# requirements-phase5.txt (additions)

neo4j==5.15.0
```

### Additional Frontend Packages

| Package | Version | Purpose |
|---------|---------|---------|
| @neo4j-nvl/react | 0.2.x | Graph visualization |
| d3 | 7.8.x | Data visualization |

```json
{
  "dependencies": {
    "@neo4j-nvl/react": "^0.2.0",
    "d3": "^7.8.5"
  }
}
```

### Neo4j Configuration

```yaml
# docker-compose addition for Phase 5
neo4j:
  image: neo4j:5.15.0-community
  ports:
    - "7474:7474"  # HTTP
    - "7687:7687"  # Bolt
  environment:
    - NEO4J_AUTH=neo4j/your_password
    - NEO4J_PLUGINS=["apoc"]
  volumes:
    - neo4j_data:/data
```

---

## Phase 6: Polish & Administration

**Goal**: Settings UI, metadata management, UX refinement

### Additional Frontend Packages

| Package | Version | Purpose |
|---------|---------|---------|
| @radix-ui/react-slider | 1.1.x | Settings sliders |
| @radix-ui/react-switch | 1.0.x | Toggle switches |
| @radix-ui/react-select | 2.0.x | Dropdowns |
| sonner | 1.3.x | Toast notifications |

```json
{
  "dependencies": {
    "@radix-ui/react-slider": "^1.1.2",
    "@radix-ui/react-switch": "^1.0.3",
    "@radix-ui/react-select": "^2.0.0",
    "sonner": "^1.3.1"
  }
}
```

---

## Phase 7: Conversation Persistence

**Goal**: Save and resume conversation sessions

No additional dependencies required - uses existing PostgreSQL and frontend stack.

### Database Additions

```sql
-- conversations table added in Phase 7
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255),
    session_id VARCHAR(100) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE conversation_messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID NOT NULL REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

---

## Complete Requirements Files

### requirements.txt (All Phases)

```txt
# =============================================================================
# PHASE 1: MVP CORE
# =============================================================================

# Web Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6
pydantic==2.6.1
pydantic-settings==2.1.0

# Database
sqlalchemy==2.0.25
psycopg2-binary==2.9.9
alembic==1.13.1

# Search
opensearch-py==2.4.2

# Task Queue
celery==5.3.6
redis==5.0.1

# Video Processing
ffmpeg-python==0.2.0

# Transcription + Speaker Diarization
whisperx>=3.1.0
pyannote.audio>=3.1.0

# Embeddings
sentence-transformers==2.6.1
torch==2.1.2

# Utilities
python-dotenv==1.0.0

# =============================================================================
# PHASE 2: CONVERSATIONAL AI
# =============================================================================

# No additional Python packages - Claude accessed via CLI

# =============================================================================
# PHASE 3: INTELLIGENT ANALYSIS
# =============================================================================

# Visual Content Analysis (Claude handles text extraction from images)
opencv-python==4.9.0.80
pillow==10.2.0

# =============================================================================
# PHASE 4: AGENTIC SEARCH
# =============================================================================

# No additional packages - uses existing FastAPI REST endpoints
# Claude accesses the API via curl commands parsed by the backend

# =============================================================================
# PHASE 5: KNOWLEDGE GRAPH
# =============================================================================

neo4j==5.15.0
```

### requirements-dev.txt

```txt
# Development and testing dependencies
-r requirements.txt

pytest==7.4.4
pytest-asyncio==0.23.3
pytest-cov==4.1.0
ruff==0.1.14
black==24.1.1
mypy==1.8.0
```

### Phase-Specific Requirements

For incremental development, use phase-specific files:

```txt
# requirements-phase1.txt
fastapi==0.109.0
uvicorn[standard]==0.27.0
python-multipart==0.0.6
pydantic==2.6.1
pydantic-settings==2.1.0
sqlalchemy==2.0.25
psycopg2-binary==2.9.9
alembic==1.13.1
opensearch-py==2.4.2
celery==5.3.6
redis==5.0.1
ffmpeg-python==0.2.0
whisperx>=3.1.0
pyannote.audio>=3.1.0
sentence-transformers==2.6.1
torch==2.1.2
python-dotenv==1.0.0
```

```txt
# requirements-phase2.txt
-r requirements-phase1.txt
# No additional Python packages - Claude accessed via CLI
```

```txt
# requirements-phase3.txt
-r requirements-phase2.txt
# Visual content analysis (Claude handles text extraction from images)
opencv-python==4.9.0.80
pillow==10.2.0
```

```bash
# Install specific phase
pip install -r requirements-phase1.txt

# Install with dev dependencies
pip install -r requirements-dev.txt
```

### package.json (All Phases)

```json
{
  "name": "whedifaqaui-frontend",
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint . --ext .ts,.tsx",
    "test": "vitest"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.22.0",
    "axios": "^1.6.7",
    "video.js": "^8.6.1",
    "@tanstack/react-query": "^5.17.0",
    "react-markdown": "^9.0.1",
    "remark-gfm": "^4.0.0",
    "@radix-ui/react-slider": "^1.1.2",
    "@radix-ui/react-switch": "^1.0.3",
    "@radix-ui/react-select": "^2.0.0",
    "sonner": "^1.3.1",
    "@neo4j-nvl/react": "^0.2.0",
    "d3": "^7.8.5"
  },
  "devDependencies": {
    "typescript": "^5.3.3",
    "vite": "^5.4.0",
    "tailwindcss": "^3.4.1",
    "@vitejs/plugin-react": "^4.2.1",
    "@types/react": "^18.2.48",
    "@types/react-dom": "^18.2.18",
    "@types/d3": "^7.4.3",
    "eslint": "^8.56.0",
    "vitest": "^1.2.2",
    "@testing-library/react": "^14.1.2"
  }
}
```

---

## Docker Configuration

### Backend Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libgl1-mesa-glx \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy and install dependencies (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose (All Services)

```yaml
version: '3.8'

services:
  # ===========================================
  # PHASE 1 SERVICES
  # ===========================================

  postgres:
    image: postgres:16.1-alpine
    environment:
      POSTGRES_USER: whedifaqaui
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: whedifaqaui
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U whedifaqaui"]
      interval: 10s
      timeout: 5s
      retries: 5

  opensearch:
    image: opensearchproject/opensearch:2.11.1
    environment:
      - discovery.type=single-node
      - DISABLE_SECURITY_PLUGIN=true
      - "OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m"
    volumes:
      - opensearch_data:/usr/share/opensearch/data
    ports:
      - "9200:9200"
    healthcheck:
      test: ["CMD-SHELL", "curl -s http://localhost:9200 >/dev/null || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5

  redis:
    image: redis:7.2.4-alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://whedifaqaui:${POSTGRES_PASSWORD}@postgres:5432/whedifaqaui
      - OPENSEARCH_URL=http://opensearch:9200
      - REDIS_URL=redis://redis:6379/0
      - WHISPER_MODEL=large-v2
      - WHISPER_DEVICE=cuda  # or 'cpu'
    volumes:
      - ./data/videos:/data/videos
      - ./data/transcripts:/data/transcripts
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      opensearch:
        condition: service_healthy
      redis:
        condition: service_healthy
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    command: celery -A app.celery worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://whedifaqaui:${POSTGRES_PASSWORD}@postgres:5432/whedifaqaui
      - OPENSEARCH_URL=http://opensearch:9200
      - REDIS_URL=redis://redis:6379/0
      - WHISPER_MODEL=large-v2
      - WHISPER_DEVICE=cuda
    volumes:
      - ./data/videos:/data/videos
      - ./data/transcripts:/data/transcripts
    depends_on:
      - redis
      - postgres
      - opensearch
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    depends_on:
      - backend

  # ===========================================
  # PHASE 5 SERVICES (add when needed)
  # ===========================================

  # neo4j:
  #   image: neo4j:5.15.0-community
  #   environment:
  #     - NEO4J_AUTH=neo4j/${NEO4J_PASSWORD}
  #     - NEO4J_PLUGINS=["apoc"]
  #   volumes:
  #     - neo4j_data:/data
  #   ports:
  #     - "7474:7474"
  #     - "7687:7687"

volumes:
  postgres_data:
  opensearch_data:
  redis_data:
  # neo4j_data:  # Phase 5
```

### Local Development Setup

```bash
# 1. Create and activate virtual environment
cd backend
python -m venv .venv
source .venv/bin/activate  # Linux/Mac
# .venv\Scripts\activate   # Windows

# 2. Install dependencies
pip install -r requirements-dev.txt

# 3. Start infrastructure
docker compose up -d postgres opensearch redis

# 4. Run migrations
alembic upgrade head

# 5. Start backend
uvicorn app.main:app --reload

# 6. Start Celery worker (separate terminal)
celery -A app.celery worker --loglevel=info

# 7. Setup frontend (separate terminal)
cd frontend
npm install
npm run dev
```

---

## Hardware Requirements

### Development Environment

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 4 cores | 8+ cores |
| RAM | 16 GB | 32 GB |
| Storage | 100 GB SSD | 500 GB NVMe |
| GPU | None (CPU mode) | NVIDIA 8GB+ VRAM |
| Node.js | 20.x LTS | 20.x LTS |
| Python | 3.11 | 3.11 |

### Production Environment

| Component | Recommended |
|-----------|-------------|
| CPU | 8+ cores |
| RAM | 32 GB |
| Storage | 1 TB NVMe SSD |
| GPU | NVIDIA RTX 3080+ (12GB VRAM) |

### GPU Impact on Processing Time (2-hour video)

| Component | With GPU | Without GPU |
|-----------|----------|-------------|
| Transcription | 10-20 min | 2-4 hours |
| Embedding generation | ~1 sec | ~30 sec |
| **Total processing** | **~25 min** | **~4 hours** |

---

## Version Compatibility Matrix

| Component | Minimum | Recommended | Max Tested |
|-----------|---------|-------------|------------|
| Python | 3.10 | 3.11 | 3.11 |
| Node.js | 18.x | 20.x LTS | 20.x LTS |
| pip | 23.0 | 23.3+ | latest |
| PostgreSQL | 15 | 16 | 16 |
| OpenSearch | 2.9 | 2.11 | 2.11 |
| Redis | 7.0 | 7.2 | 7.2 |
| CUDA | 11.8 | 12.1 | 12.1 |
| cuDNN | 8.6 | 8.9 | 8.9 |

---

## Sources

- [FastAPI Releases](https://github.com/fastapi/fastapi/releases)
- [React Versions](https://react.dev/versions)
- [Vite Releases](https://vite.dev/releases)
- [Tailwind CSS v4.0](https://tailwindcss.com/blog/tailwindcss-v4)
- [faster-whisper PyPI](https://pypi.org/project/faster-whisper/)
- [sentence-transformers Releases](https://github.com/UKPLab/sentence-transformers/releases)
- [OpenSearch Version History](https://docs.opensearch.org/latest/version-history/)
- [Celery Releases](https://github.com/celery/celery/releases)
- [Video.js Releases](https://github.com/videojs/video.js/releases)
- [Neo4j Supported Versions](https://neo4j.com/developer/kb/neo4j-supported-versions/)
