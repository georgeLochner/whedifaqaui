# System Design Overview

This document provides a high-level understanding of Whedifaqaui's architecture and serves as a guide to the detailed design documentation.

## What the System Does

Whedifaqaui transforms recorded technical meetings into an AI-searchable knowledge base. Users upload video recordings, and the system:

1. **Transcribes** speech to text with speaker identification
2. **Analyzes** content to extract entities (people, systems, projects) and their relationships
3. **Indexes** semantically-chunked segments for hybrid search
4. **Enables** natural language querying through a conversational AI interface

The goal is to answer questions like *"What did John say about the Cognito migration?"* with precise video timestamps and synthesized answers.

---

## Architecture at a Glance

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              WEB FRONTEND                                    │
│                       React + TypeScript + Tailwind                          │
│                                                                              │
│   Conversation Panel  │  Results List  │  Video Player + Transcript         │
└───────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ REST API
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            FASTAPI BACKEND                                   │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │  Query Service  │  │  Video Service  │  │   Processing Service        │  │
│  │                 │  │                 │  │                             │  │
│  │ - Hybrid search │  │ - Upload/CRUD   │  │ - Transcription (Whisper)   │  │
│  │ - Claude CLI    │  │ - Streaming     │  │ - Semantic chunking         │  │
│  │ - Quick/Deep    │  │                 │  │ - Entity extraction         │  │
│  └────────┬────────┘  └────────┬────────┘  └──────────────┬──────────────┘  │
│           │                    │                          │                  │
│           └──────────┬─────────┴──────────────────────────┘                  │
│                      │                                                       │
│              ┌───────┴───────┐                                               │
│              │ Claude Module │  ◄── All LLM interactions via single wrapper  │
│              └───────────────┘                                               │
└──────────────────────────────────────────────────────────────────────────────┘
                                    │
        ┌───────────────────────────┼───────────────────────────┐
        │                           │                           │
        ▼                           ▼                           ▼
┌───────────────┐          ┌───────────────┐          ┌────────────────────┐
│  PostgreSQL   │          │  OpenSearch   │          │   Celery + Redis   │
│               │          │               │          │                    │
│ Source of     │          │ Search index  │          │ Async processing   │
│ truth for     │  ◄────   │ (derived,     │          │ pipeline           │
│ all data      │  sync    │ rebuildable)  │          │                    │
└───────────────┘          └───────────────┘          └────────────────────┘
        │
        │ Phase 5+
        ▼
┌───────────────┐
│    Neo4j      │
│               │
│ Knowledge     │
│ graph         │
└───────────────┘
```

---

## Three Core Behaviors

The system has three primary operational modes, each documented in detail:

### 1. Ingestion (Async Processing)

When a video is uploaded, it flows through a 6-stage Celery pipeline:

```
Upload → Transcode → Transcribe → Chunk → Analyze → Index
```

Each stage runs asynchronously with retry handling. Key decisions:
- **Semantic chunking** groups transcript segments by topic similarity (not fixed size)
- **Full-transcript entity extraction** sends entire transcripts to Claude for better disambiguation
- **Dual storage**: PostgreSQL holds source data; OpenSearch provides optimized search

**Detail document**: [processing-pipeline.md](processing-pipeline.md)

### 2. Querying (Synchronous Search)

User queries are handled in two modes:

| Mode | How It Works | Latency | Use Case |
|------|--------------|---------|----------|
| **Quick** | Backend pre-fetches top 10-20 segments, sends to Claude with question | ~10-20s | Simple, direct questions |
| **Deep** | Claude iteratively requests API calls to explore the knowledge base | ~30-90s | Complex, multi-faceted research |

Both modes use **hybrid search**: vector similarity (semantic) + BM25 (keyword) + entity filtering, combined via Reciprocal Rank Fusion.

**Detail documents**: [query-flow.md](query-flow.md), [search-api.md](search-api.md)

### 3. AI Integration (Claude Wrapper)

All Claude interactions go through a single backend wrapper module (`services/claude.py`). Users interact via the web UI only; they never invoke the CLI directly.

```python
# All Claude usage follows this pattern:
from app.services.claude import claude

response = claude.query(prompt, conversation_id)
```

The wrapper handles:
- Conversation state via session IDs
- Subprocess invocation of Claude Code CLI
- Timeout and error handling

**Detail document**: [claude-integration.md](claude-integration.md)

---

## Key Design Decisions

| Decision | Rationale |
|----------|-----------|
| **Claude Code CLI, not API** | Uses existing team subscriptions; no per-token cost; session IDs provide conversation context |
| **PostgreSQL as source of truth** | OpenSearch indices are derived and rebuildable; all persistent data lives in PostgreSQL |
| **Semantic chunking** | Embedding-based boundary detection achieves ~70% better retrieval than fixed-size chunks |
| **Full-transcript entity extraction** | Single LLM call with entire transcript provides better context for disambiguation |
| **Single Claude wrapper** | All LLM interactions (search, extraction, chunking) go through one module for consistency |

---

## Design Documents

| Document | Scope | When to Read |
|----------|-------|--------------|
| [technology-stack.md](technology-stack.md) | All libraries, frameworks, and versions | First, to understand the tooling |
| [data-model.md](data-model.md) | PostgreSQL schema, OpenSearch indices | When understanding what data is stored |
| [processing-pipeline.md](processing-pipeline.md) | Async ingestion from upload to indexed | When understanding how videos are processed |
| [query-flow.md](query-flow.md) | Search request handling (Quick + Deep modes) | When understanding how queries work |
| [search-api.md](search-api.md) | REST API endpoints for Deep Mode | When implementing or extending the API |
| [claude-integration.md](claude-integration.md) | LLM wrapper module pattern | When understanding Claude interactions |
| [deployment.md](deployment.md) | Docker Compose, infrastructure | When deploying or running locally |

---

## Reading Paths

### New to the project?

1. **This overview** - understand the system at a glance
2. **[technology-stack.md](technology-stack.md)** - know what tools are used
3. **[data-model.md](data-model.md)** - understand what gets stored
4. Skim the flow documents as needed

### Implementing ingestion features?

1. **[processing-pipeline.md](processing-pipeline.md)** - the 6-stage pipeline
2. **[data-model.md](data-model.md)** - what tables are populated
3. **[claude-integration.md](claude-integration.md)** - if touching LLM-based chunking or extraction

### Implementing search features?

1. **[query-flow.md](query-flow.md)** - Quick vs Deep mode
2. **[search-api.md](search-api.md)** - API endpoints
3. **[claude-integration.md](claude-integration.md)** - how responses are generated

### Setting up the environment?

1. **[deployment.md](deployment.md)** - Docker Compose and setup
2. **[technology-stack.md](technology-stack.md)** - version requirements

---

## Phased Implementation

The system is built incrementally across 7 phases:

| Phase | Focus | Key Deliverable |
|-------|-------|-----------------|
| 1 | MVP Core | Upload → Search → Play at timestamp |
| 2 | Conversational AI | Claude chat interface (Quick mode) |
| 3 | Intelligent Analysis | Entity extraction, speaker diarization |
| 4 | Agentic Search | REST API, iterative retrieval (Deep mode) |
| 5 | Knowledge Graph | Neo4j, visualization |
| 6 | Polish & Admin | Settings UI, metadata management |
| 7 | Persistence | Conversation history |

Implementation plans for each phase are in `docs/implementation/`.

---

## Related Documentation

- **Requirements**: `docs/requirements/` - User stories, phases, glossary
- **Implementation Plans**: `docs/implementation/` - Phase-by-phase implementation details
- **Reference**: `docs/reference/` - Detailed specifications referenced from design docs
