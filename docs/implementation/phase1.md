# Phase 1: High-Level Architectural Plan

**Phase**: MVP Core
**Goal**: Upload → Transcribe → Basic Search → Play at Timestamp

---

## Phase 1 Scope

| Story | Description |
|-------|-------------|
| V1 | Upload MKV with metadata (title, date, participants, notes) |
| V2 | Automatic transcription with timestamps and speaker diarization |
| V3 | Processing status indicators |
| P1 | Embedded video player |
| P2 | Timestamp navigation (clickable, deep-linking) |
| P3 | Synchronized transcript display (with speaker labels) |
| S1 | Natural language search (hybrid: BM25 + vector) |
| S3 | Search results link directly to video timestamps |
| M1 | Video library view with status/filtering |

---

## Transcription Strategy: WhisperX

We use **WhisperX** (not plain faster-whisper) to get both transcription AND speaker diarization in a single pass:

```
Audio → WhisperX → Transcription + Speaker Labels
                        │
                        ▼
              [0:00-0:08] SPEAKER_00: "We need to discuss auth"
              [0:08-0:15] SPEAKER_01: "I agree, it's urgent"
```

**Why WhisperX?**
- Combines Whisper transcription with pyannote speaker diarization
- Single pipeline instead of two separate steps
- Speaker data available from day one (UI/search features come in Phase 3)

---

## Project Structure

```
whedifaqaui/
├── docs/                           # [EXISTS] Documentation
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI application entry
│   │   │
│   │   ├── api/                    # API Layer
│   │   │   ├── __init__.py
│   │   │   ├── routes/
│   │   │   │   ├── __init__.py
│   │   │   │   ├── videos.py       # V1, V3, M1: upload, status, list
│   │   │   │   ├── playback.py     # P1, P2, P3: video streaming, transcript
│   │   │   │   └── search.py       # S1, S3: hybrid search
│   │   │   └── deps.py             # Dependency injection
│   │   │
│   │   ├── services/               # Business Logic Layer
│   │   │   ├── __init__.py
│   │   │   ├── video.py            # Video CRUD operations
│   │   │   ├── transcription.py    # Whisper integration
│   │   │   ├── chunking.py         # Semantic chunking logic
│   │   │   ├── embedding.py        # BGE model wrapper
│   │   │   ├── search.py           # OpenSearch query builder
│   │   │   └── ffmpeg.py           # FFmpeg operations
│   │   │
│   │   ├── models/                 # Data Layer (SQLAlchemy)
│   │   │   ├── __init__.py
│   │   │   ├── video.py            # Video model
│   │   │   ├── transcript.py       # Transcript model
│   │   │   └── segment.py          # Segment/chunk model
│   │   │
│   │   ├── schemas/                # Pydantic Schemas (API contracts)
│   │   │   ├── __init__.py
│   │   │   ├── video.py            # Video request/response schemas
│   │   │   ├── transcript.py       # Transcript schemas
│   │   │   ├── segment.py          # Segment schemas
│   │   │   └── search.py           # Search request/response schemas
│   │   │
│   │   ├── tasks/                  # Async Processing (Celery)
│   │   │   ├── __init__.py
│   │   │   ├── celery_app.py       # Celery configuration
│   │   │   ├── video_processing.py # V2: FFmpeg remux/transcode
│   │   │   ├── transcription.py    # V2: Whisper transcription
│   │   │   ├── chunking.py         # Semantic chunking task
│   │   │   └── indexing.py         # OpenSearch indexing task
│   │   │
│   │   ├── core/                   # Application Core
│   │   │   ├── __init__.py
│   │   │   ├── config.py           # Settings (pydantic-settings)
│   │   │   ├── database.py         # PostgreSQL connection
│   │   │   └── opensearch.py       # OpenSearch client
│   │   │
│   │   └── migrations/             # Alembic migrations
│   │       └── versions/
│   │
│   ├── requirements.txt
│   ├── Dockerfile
│   └── alembic.ini
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx                # React entry point
│   │   ├── App.tsx                 # Router setup
│   │   │
│   │   ├── pages/                  # Page Components
│   │   │   ├── UploadPage.tsx      # V1: Upload form
│   │   │   ├── LibraryPage.tsx     # M1: Video list
│   │   │   ├── VideoPage.tsx       # P1, P2, P3: Player + transcript
│   │   │   └── SearchPage.tsx      # S1, S3: Search interface
│   │   │
│   │   ├── components/             # Reusable Components
│   │   │   ├── common/             # Generic UI
│   │   │   │   ├── Layout.tsx
│   │   │   │   ├── Navigation.tsx
│   │   │   │   └── StatusBadge.tsx # V3: Status indicators
│   │   │   │
│   │   │   ├── video/              # Video-specific
│   │   │   │   ├── VideoPlayer.tsx # P1: HTML5 player
│   │   │   │   ├── TranscriptPanel.tsx # P3: Synchronized transcript
│   │   │   │   └── TimestampLink.tsx   # P2: Clickable timestamps
│   │   │   │
│   │   │   ├── upload/             # Upload-specific
│   │   │   │   ├── UploadForm.tsx  # V1: File + metadata form
│   │   │   │   └── UploadProgress.tsx # V1: Progress indicator
│   │   │   │
│   │   │   ├── library/            # Library-specific
│   │   │   │   ├── VideoCard.tsx   # M1: Video thumbnail card
│   │   │   │   └── VideoList.tsx   # M1: Filterable list
│   │   │   │
│   │   │   └── search/             # Search-specific
│   │   │       ├── SearchBar.tsx   # S1: Query input
│   │   │       └── SearchResults.tsx # S3: Results with timestamps
│   │   │
│   │   ├── api/                    # API Client Layer
│   │   │   ├── client.ts           # Axios/fetch wrapper
│   │   │   ├── videos.ts           # Video endpoints
│   │   │   └── search.ts           # Search endpoints
│   │   │
│   │   ├── hooks/                  # Custom React Hooks
│   │   │   ├── useVideoPlayer.ts   # P1, P2: Player state
│   │   │   └── useTranscriptSync.ts # P3: Transcript synchronization
│   │   │
│   │   ├── types/                  # TypeScript Types
│   │   │   ├── video.ts
│   │   │   ├── transcript.ts
│   │   │   └── search.ts
│   │   │
│   │   └── styles/                 # Tailwind customizations
│   │       └── index.css
│   │
│   ├── package.json
│   ├── vite.config.ts
│   ├── tailwind.config.js
│   └── Dockerfile
│
├── data/                           # Persistent Storage (volume mounted)
│   ├── videos/
│   │   ├── original/               # Uploaded MKV files
│   │   ├── processed/              # Transcoded MP4 files
│   │   ├── audio/                  # Extracted WAV (temporary)
│   │   └── thumbnails/             # Generated thumbnails
│   ├── transcripts/                # WhisperX JSON output (used by Claude)
│   └── temp/                       # Temporary files for Claude context (auto-cleaned)
│
├── docker-compose.yml              # All services
├── docker-compose.dev.yml          # Development overrides
└── .env.example                    # Environment template
```

---

## Component Specification by Layer

### Backend API Layer (`api/routes/`)

| Module | Endpoints | Stories |
|--------|-----------|---------|
| `videos.py` | `POST /videos` (upload), `GET /videos` (list), `GET /videos/{id}` (detail), `GET /videos/{id}/status` | V1, V3, M1 |
| `playback.py` | `GET /videos/{id}/stream` (video file), `GET /videos/{id}/transcript` (transcript data) | P1, P2, P3 |
| `search.py` | `GET /search?q=...` (hybrid search) | S1, S3 |

### Backend Services Layer (`services/`)

| Module | Responsibility |
|--------|----------------|
| `video.py` | Video CRUD, status management, file path handling |
| `ffmpeg.py` | Remux/transcode to MP4, extract audio WAV, generate thumbnails |
| `transcription.py` | WhisperX model loading, transcription + speaker diarization |
| `chunking.py` | Semantic boundary detection, chunk creation (embedding-based) |
| `embedding.py` | BGE model wrapper, batch embedding generation |
| `search.py` | OpenSearch hybrid query construction, result ranking |

### Backend Tasks Layer (`tasks/`)

| Task | Trigger | Purpose |
|------|---------|---------|
| `video_processing` | After upload | FFmpeg remux/transcode, thumbnail, audio extraction |
| `transcription` | After video processing | WhisperX transcription + speaker diarization → JSON |
| `chunking` | After transcription | Semantic chunking → segments in DB (with speaker labels) |
| `indexing` | After chunking | Bulk index to OpenSearch |

### Backend Models Layer (`models/`)

| Model | Phase 1 Fields |
|-------|----------------|
| `Video` | id, title, file_path, processed_path, thumbnail_path, duration, recording_date, participants[], context_notes, status, error_message, created_at, updated_at |
| `Transcript` | id, video_id, full_text, language, word_count, created_at |
| `Segment` | id, transcript_id, video_id, start_time, end_time, text, speaker, chunking_method, created_at |

Note: `speaker` field is populated by WhisperX diarization (e.g., "SPEAKER_00", "SPEAKER_01"). Phase 3 adds UI to map these to actual names from the participants list.

### Frontend Pages

| Page | Route | Stories |
|------|-------|---------|
| `UploadPage` | `/upload` | V1, V3 |
| `LibraryPage` | `/` or `/library` | M1 |
| `VideoPage` | `/videos/:id` | P1, P2, P3 |
| `SearchPage` | `/search` | S1, S3 |

### Frontend Component Groups

| Group | Components | Purpose |
|-------|------------|---------|
| `common/` | Layout, Navigation, StatusBadge | Shared UI structure |
| `video/` | VideoPlayer, TranscriptPanel, TimestampLink | Playback experience |
| `upload/` | UploadForm, UploadProgress | File upload flow |
| `library/` | VideoCard, VideoList | Library browsing |
| `search/` | SearchBar, SearchResults | Search interaction |

---

## Infrastructure Services (Docker)

| Service | Image | Purpose | Port |
|---------|-------|---------|------|
| `postgres` | postgres:16.1 | Primary database | 5432 |
| `opensearch` | opensearchproject/opensearch:2.11.0 | Search index | 9200 |
| `redis` | redis:7.2 | Celery broker | 6379 |
| `backend` | Custom (FastAPI) | API server | 8000 |
| `celery-worker` | Custom (same as backend) | Async tasks | - |
| `frontend` | Custom (Vite/Nginx) | Web UI | 3000 |

---

## Data Flow

```
┌─────────────┐     POST /videos      ┌─────────────┐
│   Browser   │ ─────────────────────>│   FastAPI   │
│  (Upload)   │                       │   Backend   │
└─────────────┘                       └──────┬──────┘
                                             │
                                    Queue video_processing
                                             │
                                             ▼
┌─────────────┐                       ┌─────────────┐
│  PostgreSQL │<──────────────────────│   Celery    │
│  (videos,   │      Save status      │   Worker    │
│ transcripts,│      & records        │             │
│  segments)  │                       └──────┬──────┘
└──────┬──────┘                              │
       │                          FFmpeg → Whisper → Chunking
       │                                     │
       │                                     ▼
       │                              ┌─────────────┐
       │                              │  OpenSearch │
       └──────────────────────────────│ (segments)  │
          Index sync                  └─────────────┘
                                             │
┌─────────────┐    GET /search?q=     ┌─────┴───────┐
│   Browser   │<──────────────────────│   FastAPI   │
│  (Search)   │    Results + links    │   Backend   │
└─────────────┘                       └─────────────┘
```

---

## Processing Pipeline (Phase 1)

```
UPLOAD → VIDEO_PROCESSING → TRANSCRIPTION → CHUNKING → INDEXING → READY
         (FFmpeg)           (Whisper)       (BGE)      (OpenSearch)
```

### Status Flow

| Status | Description |
|--------|-------------|
| `uploaded` | File received, queued for processing |
| `processing` | FFmpeg remux/transcode in progress |
| `transcribing` | Whisper transcription in progress |
| `chunking` | Semantic chunking in progress |
| `indexing` | OpenSearch indexing in progress |
| `ready` | Available for search and playback |
| `error` | Processing failed (see error_message) |

---

## What's Deferred to Later Phases

| Component | Phase |
|-----------|-------|
| `services/claude.py` (Claude wrapper) | Phase 2 |
| Entity extraction & relationships | Phase 3 |
| Speaker diarization | Phase 3 |
| Deep Mode REST API | Phase 4 |
| Neo4j integration | Phase 5 |
| Conversation persistence | Phase 7 |

---

## Database Schema (Phase 1)

### videos

```sql
CREATE TABLE videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    processed_path VARCHAR(500),
    thumbnail_path VARCHAR(500),
    duration INTEGER,
    recording_date DATE NOT NULL,
    participants TEXT[],
    context_notes TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'uploaded',
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### transcripts

```sql
CREATE TABLE transcripts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    full_text TEXT NOT NULL,
    language VARCHAR(10) DEFAULT 'en',
    word_count INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(video_id)
);
```

### segments

```sql
CREATE TABLE segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transcript_id UUID NOT NULL REFERENCES transcripts(id) ON DELETE CASCADE,
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    start_time FLOAT NOT NULL,
    end_time FLOAT NOT NULL,
    text TEXT NOT NULL,
    speaker VARCHAR(100),  -- From WhisperX diarization: "SPEAKER_00", "SPEAKER_01", etc.
    chunking_method VARCHAR(20) DEFAULT 'embedding',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_segments_speaker ON segments(speaker);
```

---

## OpenSearch Index (Phase 1)

### segments_index

```json
{
  "mappings": {
    "properties": {
      "id": { "type": "keyword" },
      "video_id": { "type": "keyword" },
      "video_title": { "type": "text" },
      "transcript_id": { "type": "keyword" },
      "text": {
        "type": "text",
        "analyzer": "english"
      },
      "embedding": {
        "type": "knn_vector",
        "dimension": 768,
        "method": {
          "name": "hnsw",
          "space_type": "cosinesimil",
          "engine": "lucene"
        }
      },
      "start_time": { "type": "float" },
      "end_time": { "type": "float" },
      "speaker": { "type": "keyword" },
      "recording_date": { "type": "date" },
      "created_at": { "type": "date" }
    }
  },
  "settings": {
    "index": {
      "knn": true,
      "number_of_shards": 1,
      "number_of_replicas": 0
    }
  }
}
```
