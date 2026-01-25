# Whedifaqaui - Project Initialization

**Read this file at the start of every new Claude Code session.**

**Last Updated**: January 2025
**Status**: Phase 0 Complete - Test Specifications in Progress

---

## Project Summary

**Whedifaqaui** is a Video Knowledge Management System that:
- Ingests recorded technical meetings (MKV format)
- Transcribes with speaker diarization (WhisperX)
- Indexes with semantic chunking (embedding-based)
- Enables natural language search via web UI
- All Claude interactions go through a backend wrapper module

**Named after**: A fictional African bird that jumps above grass to locate its nest - metaphor for finding information in vast video archives.

**Use Case**: Technical project handover - finding specific information across hours of recorded meetings.

---

## Implementation Plans Created

High-level architectural plans exist for Phases 0-3:

| File | Phase | Status |
|------|-------|--------|
| `docs/implementation/phase0.md` | Environment Setup & Scaffolding | Complete |
| `docs/implementation/phase1.md` | MVP Core | Complete |
| `docs/implementation/phase2.md` | Conversational AI (Quick Mode) | Complete |
| `docs/implementation/phase3.md` | Intelligent Analysis | Complete |

**Read these files for detailed component specifications.**

---

## Test Specifications

Test specifications define acceptance criteria for each phase:

| File | Phase | Status |
|------|-------|--------|
| `docs/testing/phase1-test-specification.md` | MVP Core | Complete |
| `docs/testing/phase2-test-specification.md` | Conversational AI | Pending |
| `docs/testing/phase3-test-specification.md` | Intelligent Analysis | Pending |

### Testing Approach

- **Test resources**: YouTube video with auto-generated transcript as ground truth
- **Transcription verification**: LLM agent compares WhisperX output vs YouTube transcript
- **Fuzzy matching**: Semantic similarity (≥85%), not exact word matching
- **Screenshot verification**: Playwright MCP captures UI states for visual verification

### Test Resource Preparation

```bash
# Download test video and transcript from YouTube
./scripts/prepare-test-data.sh "<YOUTUBE_URL>"
```

This creates:
- `/data/test/videos/test_meeting_primary.mkv` - Test video
- `/data/test/expected/test_meeting_primary_ground_truth.json` - Ground truth transcript

---

## Critical Architecture Decisions

### 1. Claude Access - CLI Only, No API

**We do NOT use the `anthropic` Python library.** All Claude interactions use the Claude Code CLI invoked programmatically via subprocess:

```python
# backend/app/services/claude.py
result = subprocess.run(
    ["claude", "-p", prompt],
    cwd=PROJECT_ROOT,  # So Claude can access data files
    capture_output=True,
    text=True
)
```

### 2. Claude Input - File References (Not Inline Text)

**Never pass large text in prompts.** Instead, write data to files and reference the path:

```python
# BAD - hits command line limits
prompt = f"Analyze this: {huge_transcript_text}"

# GOOD - Claude reads the file
prompt = f"READ FILE: /data/transcripts/{video_id}.json\nAnalyze and extract entities."
```

### 3. Claude Output - Pipe-Delimited (Not JSON)

**Claude does not reliably produce valid JSON.** Use pipe-delimited format:

```
# Prompt specifies output format:
WRITE OUTPUT to: /data/temp/analysis_{video_id}.txt

Use this EXACT format:
ENTITY|name|type|description
REL|source|relation|target|timestamp
SPEAKER|label|name|confidence
FRAME|timestamp|reason
TOPIC|name
```

**Why not JSON?** Trailing commas, comments, truncation, preamble text - all break parsing.

### 4. WhisperX for Transcription + Diarization

Use **WhisperX** (not plain faster-whisper) to get transcription AND speaker labels in one pass:

```
Audio → WhisperX → Text + Speaker Labels (SPEAKER_00, SPEAKER_01)
```

### 5. Speaker Names - Display Only (Not Searchable)

Speaker name mapping is for **UI display only**, not indexed in OpenSearch:

| Stored | Indexed? | Purpose |
|--------|----------|---------|
| `segments.speaker` = "SPEAKER_00" | NO | Attribution |
| `speaker_mappings` table | NO | Display names in UI |

**For people search, use entity extraction instead** (type=person).

### 6. Single Claude Call for Content Analysis

Phase 3 uses ONE Claude call to extract everything:
- Entities + relationships
- Speaker name mapping (inferred from context)
- Critical frame timestamps (max 10)
- Topics

### 7. Critical Frames Only (No Regular Capture)

Claude identifies important visual moments from transcript context. No FFmpeg scene detection or regular interval capture.

### 8. No OCR Library

Claude reads image files directly and extracts visible text. No pytesseract.

---

## Technology Stack

| Component | Technology | Notes |
|-----------|------------|-------|
| Frontend | React 18.2 + Vite 5.4 + Tailwind 3.4 | |
| Backend | FastAPI 0.109 + Celery 5.3 | |
| Database | PostgreSQL 16.1 | Source of truth |
| Search | OpenSearch 2.11 | Derived index |
| Transcription | WhisperX | Includes speaker diarization |
| Embeddings | sentence-transformers (BGE) 2.6 | |
| LLM Access | Claude Code CLI | Via subprocess |
| Graph DB | Neo4j 5.15 | Phase 5 |

**No `anthropic` library** - removed from all requirements.

---

## Implementation Phases

| Phase | Name | Architecture | Tests | Implementation |
|-------|------|--------------|-------|----------------|
| 0 | Environment Setup & Scaffolding | Complete | N/A | **COMPLETE** |
| 1 | MVP Core | Complete | **COMPLETE** | Pending |
| 2 | Conversational AI (Quick Mode) | Complete | Pending | Pending |
| 3 | Intelligent Analysis | Complete | Pending | Pending |
| 4 | Agentic Search (Deep Mode) | Not planned | - | - |
| 5 | Knowledge Graph | Not planned | - | - |
| 6 | Polish & Administration | Not planned | - | - |
| 7 | Conversation Persistence | Not planned | - | - |

---

## Data Directory Structure

```
/data/
├── videos/
│   ├── original/           # Uploaded MKV files
│   ├── processed/          # Transcoded MP4 files
│   ├── audio/              # Extracted WAV (temporary)
│   ├── thumbnails/         # Generated thumbnails
│   └── screenshots/        # Critical frames (Phase 3)
│       └── {video_id}/
│           └── 00125.jpg   # Frame at timestamp
├── transcripts/            # WhisperX JSON output (Claude reads these)
│   └── {video_id}.json
├── temp/                   # Temporary files for Claude I/O (auto-cleaned)
│   ├── context_{uuid}.json # Search context for Quick Mode
│   └── analysis_{id}.txt   # Claude's pipe-delimited output
└── test/                   # Test resources (not committed to git)
    ├── videos/
    │   ├── test_meeting_primary.mkv  # YouTube-sourced test video
    │   ├── test_silent.mkv           # Edge case: silent audio
    │   └── test_corrupted.mkv        # Edge case: invalid file
    └── expected/
        └── test_meeting_primary_ground_truth.json  # YouTube transcript
```

---

## Pipe-Delimited Output Format

```
# Record types for content analysis
ENTITY|name|type|description
REL|source|relation|target|timestamp_seconds
SPEAKER|label|name|confidence
FRAME|timestamp_seconds|reason
TOPIC|name

# Record types for frame description
CONTENT_TYPE|type
TEXT|extracted visible text
DESC|visual description
DETAIL|technical detail
```

**Parser example:**
```python
for line in text.strip().split('\n'):
    if line.startswith('#') or not line.strip():
        continue
    parts = line.split('|')
    record_type = parts[0]
    # Switch on record_type...
```

---

## Things NOT To Do

1. **Don't use `anthropic` library** - use Claude CLI via subprocess
2. **Don't pass large text in prompts** - use file references
3. **Don't expect valid JSON from Claude** - use pipe-delimited format
4. **Don't implement MCP** - use REST API with CALL: curl pattern
5. **Don't index speaker names** - use entity search for people
6. **Don't capture frames at regular intervals** - only Claude-identified critical frames
7. **Don't add OCR library** - Claude extracts text from images
8. **Don't use bleeding-edge versions** - stick to pre-2025 versions

---

## Key Documentation Files

| File | Purpose |
|------|---------|
| `docs/implementation/phase1.md` | Phase 1 architecture + components |
| `docs/implementation/phase2.md` | Phase 2 architecture + Claude wrapper |
| `docs/implementation/phase3.md` | Phase 3 architecture + content analysis |
| `docs/testing/phase1-test-specification.md` | Phase 1 test criteria + E2E scenarios |
| `docs/architecture/claude-integration.md` | Claude wrapper module specification |
| `docs/architecture/data-model.md` | PostgreSQL + OpenSearch schemas |
| `docs/requirements/implementation-phases.md` | Phase details |
| `docs/requirements/phase-stories-matrix.md` | Stories mapped to phases |

---

## Starting a New Session

1. Read this file: `docs/initialize.md`
2. Check implementation plans: `docs/implementation/phase{0,1,2,3}.md`
3. Check test specifications: `docs/testing/phase{1,2,3}-test-specification.md`
4. Check architecture docs as needed

**Current work**: Complete test specifications for Phases 1-3, then implement.

### Phase 0 (Complete)
- Docker Compose with all infrastructure services (postgres, opensearch, redis, backend, celery-worker, frontend)
- Backend scaffolding (FastAPI, SQLAlchemy, Celery, Alembic)
- Frontend scaffolding (Vite, React, Tailwind)
- Health check endpoint at `/api/health`
- Verification script: `./scripts/verify-environment.sh`
- Start environment: `docker compose up -d`

### Phase 1 Test Specification (Complete)
- Unit tests: ~51 backend, ~29 frontend
- Integration tests: API + DB + Services
- E2E tests: 6 Playwright scenarios
- LLM verification: Transcript quality via Claude agent
- Screenshot verification: 17 checkpoints
- See `docs/testing/phase1-test-specification.md`

### Phase 1 Implementation (Next)
- Database models (Video, Segment, etc.)
- Video upload and processing pipeline
- WhisperX transcription with speaker diarization
- Basic search functionality
- See `docs/implementation/phase1.md` for full specification
