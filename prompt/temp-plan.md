# Whedifaqaui - High-Level Architecture Plan

## Project Structure

```
whedifaqaui/
├── docs/                           # Documentation (exists)
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI application entry point
│   │   ├── config.py               # Configuration management (pydantic-settings)
│   │   │
│   │   ├── api/                    # REST API layer
│   │   │   ├── __init__.py
│   │   │   ├── routes/             # Route definitions by domain
│   │   │   │   ├── videos.py       # Video upload, list, metadata (Phase 1)
│   │   │   │   ├── search.py       # Search endpoints (Phase 1, expanded P4)
│   │   │   │   ├── chat.py         # Conversational AI endpoints (Phase 2)
│   │   │   │   ├── entities.py     # Entity endpoints (Phase 3)
│   │   │   │   ├── topics.py       # Topic timeline endpoints (Phase 4)
│   │   │   │   ├── conversations.py # Conversation persistence (Phase 7)
│   │   │   │   └── settings.py     # System settings endpoints (Phase 6)
│   │   │   ├── dependencies.py     # FastAPI dependencies (auth, db sessions)
│   │   │   └── schemas/            # Pydantic request/response models
│   │   │       ├── video.py
│   │   │       ├── search.py
│   │   │       ├── chat.py
│   │   │       └── ...
│   │   │
│   │   ├── services/               # Business logic layer
│   │   │   ├── __init__.py
│   │   │   ├── claude.py           # Claude Code CLI wrapper (CRITICAL - Phase 2+)
│   │   │   ├── video.py            # Video management logic
│   │   │   ├── search.py           # Hybrid search orchestration
│   │   │   ├── embedding.py        # Embedding generation (sentence-transformers)
│   │   │   ├── indexing.py         # OpenSearch indexing operations
│   │   │   ├── entity.py           # Entity management (Phase 3)
│   │   │   ├── deep_mode.py        # Agentic search orchestration (Phase 4)
│   │   │   └── graph.py            # Neo4j operations (Phase 5)
│   │   │
│   │   ├── tasks/                  # Celery async tasks
│   │   │   ├── __init__.py
│   │   │   ├── celery_app.py       # Celery configuration
│   │   │   ├── video_processing.py # FFmpeg processing task
│   │   │   ├── transcription.py    # Whisper transcription task
│   │   │   ├── chunking.py         # Semantic chunking task
│   │   │   ├── analysis.py         # Entity extraction task (Phase 3)
│   │   │   ├── indexing.py         # OpenSearch bulk indexing task
│   │   │   └── visual.py           # Screenshot/OCR task (Phase 3)
│   │   │
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   │   ├── __init__.py
│   │   │   ├── base.py             # Base model class
│   │   │   ├── video.py            # Video model
│   │   │   ├── transcript.py       # Transcript model
│   │   │   ├── segment.py          # Segment (chunk) model
│   │   │   ├── entity.py           # Entity models (entity, mentions, relationships)
│   │   │   ├── topic.py            # Topic models
│   │   │   ├── conversation.py     # Conversation models (Phase 7)
│   │   │   └── settings.py         # System settings model
│   │   │
│   │   ├── db/                     # Database layer
│   │   │   ├── __init__.py
│   │   │   ├── session.py          # Database session management
│   │   │   └── opensearch.py       # OpenSearch client configuration
│   │   │
│   │   └── core/                   # Cross-cutting concerns
│   │       ├── __init__.py
│   │       ├── exceptions.py       # Custom exceptions
│   │       └── logging.py          # Logging configuration
│   │
│   ├── migrations/                 # Alembic migrations
│   │   ├── versions/
│   │   └── alembic.ini
│   │
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── conftest.py
│   │
│   ├── requirements.txt
│   ├── requirements-dev.txt
│   └── Dockerfile
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx                # Application entry point
│   │   ├── App.tsx                 # Root component with routing
│   │   │
│   │   ├── components/             # Reusable UI components
│   │   │   ├── common/             # Generic components
│   │   │   │   ├── Button/
│   │   │   │   ├── Input/
│   │   │   │   ├── Modal/
│   │   │   │   └── Loading/
│   │   │   │
│   │   │   ├── video/              # Video-related components
│   │   │   │   ├── VideoPlayer/    # Video.js wrapper
│   │   │   │   ├── TranscriptView/ # Synchronized transcript display
│   │   │   │   ├── UploadForm/     # Video upload with metadata
│   │   │   │   └── VideoCard/      # Library item card
│   │   │   │
│   │   │   ├── search/             # Search components
│   │   │   │   ├── SearchBar/
│   │   │   │   ├── SearchResults/
│   │   │   │   └── ResultItem/
│   │   │   │
│   │   │   ├── chat/               # Chat interface (Phase 2)
│   │   │   │   ├── ChatPanel/      # Main conversation panel
│   │   │   │   ├── MessageBubble/
│   │   │   │   └── CitationLink/
│   │   │   │
│   │   │   ├── workspace/          # Three-panel layout (Phase 2)
│   │   │   │   ├── ResultsList/    # Accumulated results
│   │   │   │   └── ContentPane/    # Selected content display
│   │   │   │
│   │   │   ├── entity/             # Entity display (Phase 3)
│   │   │   │   └── EntityCard/
│   │   │   │
│   │   │   └── graph/              # Knowledge graph (Phase 5)
│   │   │       └── GraphViewer/
│   │   │
│   │   ├── pages/                  # Page-level components
│   │   │   ├── HomePage/           # Landing / dashboard
│   │   │   ├── LibraryPage/        # Video library (Phase 1)
│   │   │   ├── UploadPage/         # Video upload (Phase 1)
│   │   │   ├── VideoPage/          # Single video view (Phase 1)
│   │   │   ├── SearchPage/         # Search interface (Phase 1)
│   │   │   ├── WorkspacePage/      # Three-panel AI workspace (Phase 2)
│   │   │   ├── EntityPage/         # Entity detail view (Phase 3)
│   │   │   ├── GraphPage/          # Knowledge graph view (Phase 5)
│   │   │   └── SettingsPage/       # System settings (Phase 6)
│   │   │
│   │   ├── services/               # API client layer
│   │   │   ├── api.ts              # Axios instance configuration
│   │   │   ├── videoService.ts     # Video API calls
│   │   │   ├── searchService.ts    # Search API calls
│   │   │   ├── chatService.ts      # Chat API calls (Phase 2)
│   │   │   ├── entityService.ts    # Entity API calls (Phase 3)
│   │   │   └── settingsService.ts  # Settings API calls (Phase 6)
│   │   │
│   │   ├── hooks/                  # Custom React hooks
│   │   │   ├── useVideoPlayer.ts
│   │   │   ├── useSearch.ts
│   │   │   ├── useChat.ts          # (Phase 2)
│   │   │   └── useConversation.ts  # (Phase 7)
│   │   │
│   │   ├── store/                  # State management (if needed)
│   │   │   └── ...
│   │   │
│   │   ├── types/                  # TypeScript type definitions
│   │   │   ├── video.ts
│   │   │   ├── search.ts
│   │   │   ├── chat.ts
│   │   │   └── entity.ts
│   │   │
│   │   └── styles/                 # Global styles
│   │       └── globals.css
│   │
│   ├── public/
│   ├── package.json
│   ├── tsconfig.json
│   ├── tailwind.config.js
│   ├── vite.config.ts
│   └── Dockerfile
│
├── data/                           # Data volumes (gitignored)
│   ├── videos/
│   │   ├── original/               # Uploaded MKV files
│   │   ├── processed/              # Transcoded MP4 files
│   │   ├── audio/                  # Extracted audio (temporary)
│   │   └── thumbnails/             # Generated thumbnails
│   └── transcripts/                # JSON transcript files
│
├── scripts/                        # Utility scripts
│   ├── init_opensearch.py          # Create OpenSearch indices
│   ├── seed_data.py                # Development seed data
│   └── reindex.py                  # Rebuild OpenSearch from PostgreSQL
│
├── docker-compose.yml              # Development environment
├── docker-compose.prod.yml         # Production environment
├── .env.example
└── .gitignore
```

---

## Component Specification by Layer

### Backend Services Layer

| Service | Responsibility | Phase | Dependencies |
|---------|---------------|-------|--------------|
| **ClaudeService** | CLI wrapper for all LLM interactions | 2 | subprocess, uuid |
| **VideoService** | Video CRUD, metadata management | 1 | models.video, db |
| **SearchService** | Hybrid search orchestration | 1 | OpenSearch, EmbeddingService |
| **EmbeddingService** | Generate embeddings via sentence-transformers | 1 | sentence-transformers |
| **IndexingService** | Sync PostgreSQL → OpenSearch | 1 | OpenSearch, models |
| **EntityService** | Entity CRUD, relationships, mentions | 3 | models.entity, SearchService |
| **DeepModeService** | Agentic search loop orchestration | 4 | ClaudeService, SearchService |
| **GraphService** | Neo4j operations | 5 | neo4j driver |

### Backend Tasks Layer (Celery)

| Task | Responsibility | Phase | Dependencies |
|------|---------------|-------|--------------|
| **process_video** | FFmpeg remux/transcode, thumbnail, audio extract | 1 | ffmpeg-python |
| **transcribe_video** | Whisper transcription | 1 | faster-whisper |
| **semantic_chunk** | Chunk transcript with embeddings | 1 | EmbeddingService |
| **analyze_content** | Entity extraction via Claude | 3 | ClaudeService |
| **index_video** | Bulk index to OpenSearch | 1 | IndexingService |
| **extract_visuals** | Screenshot + OCR | 3 | opencv, pytesseract |

### Backend API Routes

| Route Module | Endpoints | Phase |
|-------------|-----------|-------|
| **videos** | POST /upload, GET /videos, GET /videos/{id}, PATCH /videos/{id}, DELETE /videos/{id} | 1/6 |
| **search** | GET /search, GET /search/speaker/{name}, GET /search/date-range | 1/4 |
| **chat** | POST /chat (Quick Mode), POST /chat/deep (Deep Mode) | 2/4 |
| **entities** | GET /entities/{name}, GET /entities | 3/4 |
| **topics** | GET /topics/{name}/timeline | 4 |
| **segments** | GET /segments/{id}/context, GET /videos/{id}/transcript | 4 |
| **conversations** | GET /conversations, POST /conversations, DELETE /conversations/{id} | 7 |
| **settings** | GET /settings, PATCH /settings | 6 |

### Backend Data Models

| Model | Key Fields | Phase |
|-------|-----------|-------|
| **Video** | id, title, file_path, processed_path, duration, recording_date, participants, status | 1 |
| **Transcript** | id, video_id, full_text, language | 1 |
| **Segment** | id, transcript_id, video_id, start_time, end_time, text, speaker, chunking_method | 1 |
| **Entity** | id, name, canonical_name, type, description, aliases, mention_count | 3 |
| **EntityMention** | id, entity_id, segment_id, video_id, timestamp | 3 |
| **EntityRelationship** | id, source_entity_id, target_entity_id, relation_type, video_id | 3 |
| **Topic** | id, name, description, parent_topic_id | 3 |
| **TopicMention** | id, topic_id, segment_id, video_id | 3 |
| **SystemSettings** | key, value (JSONB) | 1 |
| **Conversation** | id, title, session_id, created_at | 7 |
| **ConversationMessage** | id, conversation_id, role, content, created_at | 7 |

### Frontend Pages

| Page | Purpose | Phase |
|------|---------|-------|
| **LibraryPage** | List all videos with status, search/filter | 1 |
| **UploadPage** | Upload form with metadata fields | 1 |
| **VideoPage** | Video player + synchronized transcript | 1 |
| **SearchPage** | Basic search interface | 1 |
| **WorkspacePage** | Three-panel AI workspace (chat/results/content) | 2 |
| **EntityPage** | Entity detail with relationships | 3 |
| **GraphPage** | Interactive knowledge graph visualization | 5 |
| **SettingsPage** | System configuration UI | 6 |

### Frontend Components (Key)

| Component | Purpose | Phase |
|-----------|---------|-------|
| **VideoPlayer** | Video.js wrapper with timestamp seeking | 1 |
| **TranscriptView** | Scrollable transcript with click-to-seek | 1 |
| **UploadForm** | File upload + metadata input | 1 |
| **SearchResults** | Paginated results with snippets | 1 |
| **ChatPanel** | Conversation interface with history | 2 |
| **ResultsList** | Accumulated session results | 2 |
| **ContentPane** | Selected content display area | 2 |
| **GraphViewer** | Neo4j visualization (d3/nvl) | 5 |

---

## Infrastructure Components

| Component | Technology | Purpose |
|-----------|------------|---------|
| **PostgreSQL** | postgres:16.1-alpine | Source of truth for all data |
| **OpenSearch** | opensearchproject/opensearch:2.11.1 | Hybrid search indices |
| **Redis** | redis:7.2.4-alpine | Celery broker + result backend |
| **Neo4j** | neo4j:5.15.0-community | Knowledge graph (Phase 5) |

---

## Data Flow Summary

```
Upload Flow (Phase 1):
Web UI → POST /upload → [PostgreSQL: video created]
    → Celery: process_video → Celery: transcribe_video
    → Celery: semantic_chunk → Celery: index_video
    → [OpenSearch: segments indexed] → Status: READY

Quick Query Flow (Phase 2):
Web UI → POST /chat → [Generate embedding]
    → [OpenSearch: hybrid search] → [Prepare context]
    → [ClaudeService.query()] → Response with citations

Deep Query Flow (Phase 4):
Web UI → POST /chat/deep → [Claude with API docs]
    → Loop: [Claude CALL:] → [Execute API] → [Feed back]
    → Final answer with citations
```

---

## Key Architectural Decisions Reflected

1. **Claude CLI Wrapper**: All LLM access through `services/claude.py` - never direct `anthropic` library
2. **REST API for Deep Mode**: Claude uses `CALL: curl` pattern, not MCP
3. **Dual Database**: PostgreSQL (truth) + OpenSearch (search) with unidirectional sync
4. **Celery Pipeline**: Each processing stage is an independent task for resilience
5. **Phase-Gated Features**: Structure supports incremental delivery
