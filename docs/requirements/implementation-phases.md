# Implementation Phases

This document outlines the phased delivery plan for Whedifaqaui, prioritizing an end-to-end testable MVP as early as possible.

## Phase Overview

| Phase | Name | Goal |
|-------|------|------|
| 1 | MVP Core | Upload → Transcribe → Basic Search → Play at Timestamp |
| 2 | Conversational AI (Simple) | Pre-fetched context, quick answers, results workspace |
| 3 | Intelligent Analysis | Entity extraction, visual content, speaker identification |
| 4 | **Agentic Search** | REST API, iterative retrieval, deep research mode |
| 5 | Knowledge Graph | Neo4j, visualization, timelines, curation |
| 6 | Polish & Admin | Video management and UX refinement |
| 7 | Persistence | Conversation history across sessions |

---

## Phase 1: Minimal End-to-End (MVP Core)

**Goal**: A working system where you can upload a video, have it transcribed, search the transcript, and click to play at the relevant moment.

### User Stories Included

| ID | Story | Description |
|----|-------|-------------|
| V1 | Video Upload | Upload MKV with metadata through web UI |
| V2 | Auto Transcription | Automatic transcription with timestamps |
| V3 | Processing Status | Status indicators (uploading → transcribing → ready) |
| P1 | Video Player | Embedded playback with standard controls |
| P2 | Timestamp Navigation | Clickable timestamps, deep-linking |
| P3 | Synchronized Transcript | Transcript display alongside video |
| S1 | Natural Language Search | Basic intent-based search |
| S3 | Timestamp Links | Search results link directly to video moments |
| M1 | Video Library | List view of all videos with status |

### Key Deliverables
- Web frontend with upload and search sections
- Video storage on server
- Transcription pipeline (FFmpeg + faster-whisper)
- Basic hybrid search (OpenSearch)
- Video playback with transcript sync

### Success Criteria
- User can upload a video and see processing status
- Transcription completes automatically
- User can search and find relevant content
- Clicking a result navigates to the correct timestamp

---

## Phase 2: Conversational AI (Simple/Quick Mode)

**Goal**: Transform basic search into an AI-powered conversational experience with pre-fetched context and a dynamic results workspace.

### User Stories Included

| ID | Story | Description |
|----|-------|-------------|
| S7 | Conversational Search | Chat-style AI interaction with context memory |
| S8 | Results List | Scrollable list of accumulated findings |
| S9 | Content Pane | Click-to-view in dedicated content area |
| S2 | AI Summaries | Synthesized answers citing multiple sources |
| S10 | Document Generation | Generate and download summary documents |
| V4 | Date Tracking | Recording date for temporal relevance |

### Key Deliverables
- Three-panel UI (conversation / results / content)
- Claude Code CLI integration (pre-fetched context)
- Summary document generation
- Session-based result accumulation

### Architecture
```
User Question
     │
     ▼
Backend: Hybrid Search (OpenSearch)
     │
     ▼
Backend: Prepare Context (top 10-20 segments)
     │
     ▼
Claude Code CLI: Synthesize Answer
     │
     ▼
Response with Citations
```

### Success Criteria
- User can have multi-turn conversation with AI
- AI references previous context ("the second video")
- Results accumulate in list, clickable to view
- Summary documents can be generated and downloaded
- Response time: ~10-20 seconds

---

## Phase 3: Intelligent Analysis

**Goal**: Enrich content understanding through entity extraction, visual analysis, and speaker identification.

### User Stories Included

| ID | Story | Description |
|----|-------|-------------|
| A3 | Entity Extraction | Extract people, projects, systems, dates |
| S4 | Entity Search | Search by specific entities |
| S6 | Fuzzy Matching | Handle typos and variations |
| A1 | Visual Content | Screenshot extraction and analysis |
| P4 | Visual Display | Show screenshots in timeline |
| A2 | Speaker ID | Identify and label speakers |
| A4 | Topic Understanding | Deep content analysis |

### Key Deliverables
- Entity extraction pipeline (LLM-based)
- Entity normalization and linking
- Fuzzy search integration
- Screenshot extraction at key moments
- OCR and image description
- Speaker diarization (WhisperX)

### Architecture Additions
```
Processing Pipeline (extended):
     │
     ├── Entity Extraction (Claude API / local LLM)
     │   └── Entities table + entity_mentions
     │
     ├── Screenshot Analysis
     │   └── Key frame extraction + OCR + descriptions
     │
     └── Speaker Diarization
         └── Speaker labels on segments
```

### Success Criteria
- Entities extracted and searchable
- "Everything about [project]" queries work
- Visual content captured and described
- Speakers attributed in transcript

---

## Phase 4: Agentic Search (Deep Research Mode)

**Goal**: Enable Claude to iteratively search and gather context using REST API endpoints, providing comprehensive answers to complex questions.

### New Capabilities

| Capability | Description |
|------------|-------------|
| Search API | REST endpoints for data retrieval |
| API-based Retrieval | Claude requests API calls via curl |
| Iterative Research | Multiple search rounds |
| Deep Research Mode | User option for thorough investigation |

### API Endpoints

| Endpoint | Purpose |
|----------|---------|
| `GET /api/search` | Semantic + keyword search |
| `GET /api/search/speaker/{name}` | Filter by who said it |
| `GET /api/search/date-range` | Filter by recording date |
| `GET /api/entities/{name}` | Entity details + relationships |
| `GET /api/videos/{id}/transcript` | Full transcript of one video |
| `GET /api/segments/{id}/context` | Expand context around a segment |
| `GET /api/videos` | Browse available videos |
| `GET /api/topics/{name}/timeline` | Chronological view of topic |

### Key Deliverables
- Search API endpoints
- API documentation for Claude context prompt
- Deep research endpoint with iteration loop
- UI toggle for Quick vs Deep mode
- Progress indication for research

### Architecture
```
User Question (Deep Mode)
     │
     ▼
Backend: Invoke Claude with API Documentation
     │
     ▼
Claude: Iterative Research (loop)
     ├── CALL: curl '/api/search?query=topic'
     ├── CALL: curl '/api/search/speaker/John?query=topic'
     ├── CALL: curl '/api/entities/cognito'
     └── ... (3-8 API calls typical)
     │
     ▼ (Backend parses CALL:, executes, feeds back)
     │
Claude: Synthesize Comprehensive Answer
     │
     ▼
Response with Citations
```

### Why After Phase 3?
- Entity extraction enables `get_entity_info` tool
- Speaker diarization enables `search_by_speaker` tool
- Topic extraction enables `get_topic_timeline` tool

### Success Criteria
- Claude can iteratively search the knowledge base
- Complex questions get comprehensive answers
- Response time: ~30-90 seconds (acceptable for deep research)
- Users can choose between Quick and Deep modes

---

## Phase 5: Knowledge Graph & Curation

**Goal**: Build an evolving domain model with Neo4j and enable user curation of content.

### User Stories Included

| ID | Story | Description |
|----|-------|-------------|
| K1 | Knowledge Graph | Evolving concept/relationship model |
| K2 | Graph Visualization | Visual exploration of domain |
| K3 | Topic Timeline | Chronological view of topic evolution |
| S5 | Temporal Queries | Date-based questions |
| K4 | Currency Detection | Identify superseded information |
| U1 | Transcript Editing | Correct transcription errors |
| U2 | Comments | Timestamped user annotations |
| U3 | Deprecation | Mark outdated content |
| U4 | Entity Correction | Fix entity extraction errors |

### Key Deliverables
- Neo4j integration (Docker)
- Knowledge graph sync from PostgreSQL
- Graph visualization UI
- Timeline views
- Transcript editing interface
- Comment system
- Deprecation workflow
- Entity management UI

### Architecture Additions
```
PostgreSQL ──sync──► Neo4j
     │                  │
     │                  └── Graph queries (Cypher)
     │                  └── Relationship traversal
     │                  └── Visual exploration
     │
     └── Entity relationships table
         (source → relationship → target)
```

### Success Criteria
- Knowledge graph populated from all videos
- Users can visually explore domain concepts
- Topic timelines show evolution
- Users can correct and annotate content

---

## Phase 6: Polish & Administration

**Goal**: Complete video management capabilities and refine user experience.

### User Stories Included

| ID | Story | Description |
|----|-------|-------------|
| M2 | Metadata Editing | Update video metadata after upload |
| M3 | Video Deletion | Remove videos with proper cleanup |

### Key Deliverables
- Edit video metadata UI
- Delete with confirmation and cleanup
- Performance optimization
- UX refinement based on usage feedback

### Success Criteria
- Full CRUD operations on videos
- System performs well with growing library
- User workflows are smooth and intuitive

---

## Phase 7: Conversation Persistence

**Goal**: Enable users to save and resume conversation sessions.

### User Stories Included

| ID | Story | Description |
|----|-------|-------------|
| C1 | Conversation History | Save conversations across sessions |
| C2 | Organization | Name and manage saved conversations |

### Key Deliverables
- Conversation persistence storage
- Conversation list and management UI
- Resume conversation functionality

### Success Criteria
- Users can close browser and return to conversation
- Previous results and context preserved
- Conversations can be named and organized

---

## Dependency Diagram

```
Phase 1 (MVP Core)
    │
    ▼
Phase 2 (Conversational AI - Simple)
    │
    ▼
Phase 3 (Intelligent Analysis)
    │
    ├─────────────────────────────┐
    ▼                             ▼
Phase 4 (Agentic Search)    Phase 5 (Knowledge Graph)
    │                             │
    └─────────────┬───────────────┘
                  ▼
              Phase 6 (Polish)
                  │
                  ▼
              Phase 7 (Persistence)
```

**Notes:**
- Phase 4 (Agentic) and Phase 5 (Knowledge Graph) can be developed in parallel after Phase 3
- Phase 4 depends on Phase 3 for entity and speaker data
- Phase 5 depends on Phase 3 for entity relationships

---

## Query Mode Comparison

| Aspect | Quick Mode (Phase 2) | Deep Mode (Phase 4) |
|--------|---------------------|---------------------|
| Implementation | Pre-fetched context | REST API calls |
| Latency | ~10-20 seconds | ~30-90 seconds |
| Best for | Simple, direct questions | Complex, multi-faceted questions |
| Token usage | Fixed | Variable (higher) |
| Search strategy | Backend decides | Claude decides |
