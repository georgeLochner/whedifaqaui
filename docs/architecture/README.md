# Whedifaqaui - Technical Architecture

## Overview

Whedifaqaui is a Video Knowledge Management System that transforms recorded meetings into a searchable, AI-powered knowledge base. The architecture is designed to support:

- Video ingestion and transcription
- Hybrid search (semantic + keyword)
- AI-powered conversational queries via Claude Code CLI
- Evolving knowledge graph (Phase 5)

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              WEB FRONTEND                                    │
│                       React + TypeScript + Vite + Tailwind                   │
│   ┌───────────────┐   ┌───────────────┐   ┌─────────────────────────────┐   │
│   │ Conversation  │   │ Results List  │   │       Content Pane          │   │
│   │    Panel      │   │               │   │  (Video Player / Document)  │   │
│   └───────┬───────┘   └───────────────┘   └─────────────────────────────┘   │
└───────────┼─────────────────────────────────────────────────────────────────┘
            │
            │ REST API (HTTP)
            ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                            FASTAPI BACKEND                                   │
│                                                                              │
│  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────────────────┐  │
│  │  Query Service  │  │  Video Service  │  │   Processing Service        │  │
│  │                 │  │                 │  │                             │  │
│  │ - Hybrid search │  │ - Upload        │  │ - FFmpeg (video)            │  │
│  │ - Context prep  │  │ - Library CRUD  │  │ - Whisper (transcription)   │  │
│  │ - Claude CLI    │  │ - Streaming     │  │ - Embeddings                │  │
│  └────────┬────────┘  └────────┬────────┘  │ - Entity extraction         │  │
│           │                    │           └──────────────┬──────────────┘  │
│           │                    │                          │                  │
└───────────┼────────────────────┼──────────────────────────┼──────────────────┘
            │                    │                          │
            ▼                    ▼                          ▼
┌───────────────────┐  ┌───────────────────┐  ┌────────────────────────────────┐
│    OpenSearch     │  │    PostgreSQL     │  │      Celery + Redis            │
│                   │  │                   │  │                                │
│ - Segment index   │  │ - Videos          │  │ - Video processing tasks       │
│ - Vector (kNN)    │  │ - Transcripts     │  │ - Transcription tasks          │
│ - BM25 (keyword)  │  │ - Entities        │  │ - Indexing tasks               │
│ - Entity index    │  │ - Relationships   │  │                                │
└───────────────────┘  └───────────────────┘  └────────────────────────────────┘
                                │
                                │ (Phase 4)
                                ▼
                       ┌───────────────────┐
                       │      Neo4j        │
                       │                   │
                       │ - Knowledge Graph │
                       │ - Visualization   │
                       └───────────────────┘

┌─────────────────────────────────────────────────────────────────────────────┐
│                            FILE SYSTEM                                       │
│                                                                              │
│   /data/videos/original/     - Uploaded MKV files                           │
│   /data/videos/processed/    - Transcoded MP4 files                         │
│   /data/videos/audio/        - Extracted audio for transcription            │
│   /data/videos/thumbnails/   - Video preview images                         │
│   /data/transcripts/         - Raw transcript files                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Key Design Decisions

### 1. Hybrid Search Architecture

We combine three search strategies for optimal retrieval:

| Strategy | Technology | Purpose |
|----------|------------|---------|
| **Semantic Search** | OpenSearch kNN + embeddings | Find conceptually similar content |
| **Keyword Search** | OpenSearch BM25 | Exact matches for names, terms |
| **Entity Filtering** | OpenSearch + PostgreSQL | Filter by speaker, system, date |

Results are combined using Reciprocal Rank Fusion (RRF).

### 2. Dual Query Modes

We support two query modes to balance speed and thoroughness:

| Mode | Implementation | Latency | Best For |
|------|----------------|---------|----------|
| **Quick** (Phase 2) | Pre-fetched context → Claude | ~10-20s | Simple questions |
| **Deep** (Phase 4) | Claude with REST API | ~30-90s | Complex research |

### 3. Claude Code CLI as Query Agent

Instead of building custom LLM orchestration, we leverage Claude Code CLI:

- Uses existing team subscriptions (no API costs)
- Session IDs maintain conversation context
- Full Claude reasoning capabilities
- **Quick mode**: Backend prepares context, Claude synthesizes answers
- **Deep mode**: Claude requests API calls to iteratively search

### 3. Embedding Strategy

We generate embeddings for multiple content types:

| Content | Purpose | Indexed In |
|---------|---------|------------|
| Transcript segments | Fine-grained retrieval | OpenSearch |
| Entity descriptions | Entity search | OpenSearch |
| Segment summaries | Concept-level search | OpenSearch (Phase 2) |

### 4. Phased Database Approach

| Phase | Databases | Purpose |
|-------|-----------|---------|
| 1-3 | PostgreSQL + OpenSearch | Core functionality |
| 4+ | + Neo4j | Knowledge graph visualization |

## Documentation Index

| Document | Description |
|----------|-------------|
| [Technology Stack](technology-stack.md) | Detailed technology choices and versions |
| [Data Model](data-model.md) | PostgreSQL schema and OpenSearch indices |
| [Processing Pipeline](processing-pipeline.md) | Video ingestion and analysis workflow |
| [Query Flow](query-flow.md) | How user queries are processed (Quick + Deep modes) |
| [Search API](search-api.md) | REST API endpoints for agentic search |
| [Deployment](deployment.md) | Docker Compose configuration |

## Non-Functional Requirements

| Requirement | Target | Notes |
|-------------|--------|-------|
| Video processing | < 1 hour for 2hr video | Depends on GPU availability |
| Search latency | < 2 seconds | Hybrid search + context prep |
| Query response | < 30 seconds | Includes Claude CLI invocation |
| Concurrent users | Low (team use) | Not a high-scale system |
| Storage | ~2GB per hour of video | Includes original + processed |
