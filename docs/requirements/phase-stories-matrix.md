# Phase-Stories Matrix

This document consolidates implementation phases with their associated user stories for clear tracking.

---

## Summary

| Phase | Name | Story Count | Story IDs |
|-------|------|-------------|-----------|
| 1 | MVP Core | 9 | V1, V2, V3, P1, P2, P3, S1, S3, M1 |
| 2 | Conversational AI | 6 | S7, S8, S9, S2, S10, V4 |
| 3 | Intelligent Analysis | 7 | A1, A2, A3, A4, S4, S6, P4 |
| 4 | Agentic Search | 0 | *(Infrastructure only - REST API)* |
| 5 | Knowledge Graph | 9 | K1, K2, K3, K4, S5, U1, U2, U3, U4 |
| 6 | Polish & Admin | 3 | M2, M3, M4 |
| 7 | Conversation Persistence | 2 | C1, C2 |
| **Total** | | **36** | |

---

## Phase 1: MVP Core

**Goal**: Upload → Transcribe → Basic Search → Play at Timestamp

### V1: Video Upload
- **As a** Content Admin
- **I want to** upload video files (MKV) through a web interface
- **So that** they can be processed by the system
- **Acceptance Criteria:**
  - Upload form accepts MKV files
  - Progress indicator during upload
  - Can add title, date, participant names, and context notes

### V2: Automatic Transcription
- **As a** Content Admin
- **I want** the system to automatically transcribe uploaded videos
- **So that** spoken content becomes searchable
- **Acceptance Criteria:**
  - Transcription generated automatically
  - Timestamps preserved for each segment
  - Handles accented English (European, African, Indian speakers)

### V3: Processing Status
- **As a** Content Admin
- **I want to** see processing status
- **So that** I know when a video is ready for use
- **Acceptance Criteria:**
  - Status indicators: uploading, transcribing, analyzing, ready
  - Notification/indication when complete

### P1: Embedded Video Player
- **As a** Knowledge Seeker
- **I want to** play videos directly in the web interface
- **So that** I don't need external tools
- **Acceptance Criteria:**
  - Embedded video player
  - Standard controls (play, pause, seek, volume)
  - Supports MKV format

### P2: Timestamp Navigation
- **As a** Knowledge Seeker
- **I want to** jump to specific timestamps
- **So that** I can go directly to relevant content
- **Acceptance Criteria:**
  - Clickable timestamps throughout interface
  - URL deep-linking to timestamp (shareable)

### P3: Synchronized Transcript
- **As a** Knowledge Seeker
- **I want to** see the transcript alongside the video
- **So that** I can read while watching
- **Acceptance Criteria:**
  - Synchronized transcript display
  - Current segment highlighted
  - Click transcript to jump to that moment

### S1: Natural Language Queries
- **As a** Knowledge Seeker
- **I want to** ask questions in natural language
- **So that** I don't need to know specific keywords
- **Acceptance Criteria:**
  - Free-text query input
  - System interprets intent (not just keyword matching)
  - Handles conceptual questions ("How does X work?")

### S3: Timestamp Links
- **As a** Knowledge Seeker
- **I want** search results to include direct links to video timestamps
- **So that** I can verify/explore source material
- **Acceptance Criteria:**
  - Each citation includes clickable timestamp
  - Click navigates to that moment in video player

### M1: Video Library View
- **As a** Content Admin
- **I want to** see a list of all videos with their status and metadata
- **So that** I can manage the library
- **Acceptance Criteria:**
  - Video library view
  - Sortable/filterable by date, status, topic
  - Quick access to edit metadata

---

## Phase 2: Conversational AI (Quick Mode)

**Goal**: Pre-fetched context, quick answers, results workspace

### S7: Conversational Search
- **As a** Knowledge Seeker
- **I want to** have a conversation with an AI agent
- **So that** I can ask follow-up questions and refine my search
- **Acceptance Criteria:**
  - Chat-style conversation history
  - AI remembers context within session
  - Can reference previous results ("the second video")

### S8: Results List
- **As a** Knowledge Seeker
- **I want** the AI to add results to a scrollable results list
- **So that** I can see all findings accumulated during my session
- **Acceptance Criteria:**
  - Results list persists during session
  - Each result is clickable
  - Results can be video timestamps or generated documents

### S9: Content Pane
- **As a** Knowledge Seeker
- **I want to** click a result to view it in a content pane
- **So that** I can examine details without losing context
- **Acceptance Criteria:**
  - Content pane shows video player or document
  - Video jumps to specified timestamp
  - Documents have download option

### S2: AI-Generated Summaries
- **As a** Knowledge Seeker
- **I want to** receive AI-generated summary answers
- **So that** I get synthesized knowledge, not just links
- **Acceptance Criteria:**
  - Summary answers based on relevant content
  - Cites sources with video + timestamp
  - Synthesizes across multiple videos when relevant

### S10: Summary Document Generation
- **As a** Knowledge Seeker
- **I want to** ask the AI to summarize specific content and receive a downloadable document
- **So that** I can save and share findings
- **Acceptance Criteria:**
  - "Summarize the second video" generates document
  - Document added to results list
  - Viewable and downloadable

### V4: Recording Date Association
- **As a** Content Admin
- **I want to** associate a recording date with each video
- **So that** the system can track information currency
- **Acceptance Criteria:**
  - Date field (required) on upload
  - System uses date for temporal relevance

---

## Phase 3: Intelligent Analysis

**Goal**: Entity extraction, visual content, speaker identification

### A1: Visual Content Capture
- **As** the system
- **I want to** identify key visual moments in videos
- **So that** important diagrams/screens/slides are captured
- **Acceptance Criteria:**
  - AI identifies moments likely to contain important visual content
  - Screenshots extracted at key points
  - Screenshots analyzed (OCR for text, descriptions for diagrams)

### A2: Speaker Identification
- **As** the system
- **I want to** attempt speaker identification
- **So that** statements can be attributed
- **Acceptance Criteria:**
  - Speakers labeled (Speaker 1, Speaker 2, or by name if identifiable)
  - Transcript segments tagged with speaker

### A3: Entity Extraction
- **As** the system
- **I want to** extract entities (people, projects, systems, dates) from content
- **So that** they become searchable facets
- **Acceptance Criteria:**
  - Named entities extracted from transcript
  - Entities normalized (variations to canonical form)
  - Entities linked to timestamps where mentioned

### A4: Topic Understanding
- **As** the system
- **I want to** analyze content to understand topics and concepts
- **So that** I can build domain knowledge
- **Acceptance Criteria:**
  - AI summarizes key topics per video
  - Concepts extracted and categorized
  - Relationships between concepts identified

### S4: Entity Search
- **As a** Knowledge Seeker
- **I want to** search for specific entities (person, system, project)
- **So that** I can find all related content
- **Acceptance Criteria:**
  - Entity search/filter
  - "Everything about [payment system]"
  - "Everything [John] discussed"

### S6: Fuzzy Matching
- **As a** Knowledge Seeker
- **I want** fuzzy matching
- **So that** minor spelling variations or typos still find results
- **Acceptance Criteria:**
  - Approximate matching
  - Technical terms with common misspellings handled

### P4: Visual Content Display
- **As a** Knowledge Seeker
- **I want to** see extracted screenshots and their descriptions at relevant points
- **So that** I understand visual content without scrubbing
- **Acceptance Criteria:**
  - Visual content thumbnails shown in timeline
  - Descriptions/OCR text displayed
  - Clickable to navigate

---

## Phase 4: Agentic Search (Deep Mode)

**Goal**: REST API endpoints for iterative retrieval and deep research

### Infrastructure Deliverables (No User Stories)

This phase implements the search API endpoints that enable Claude to iteratively search:

| Tool | Purpose |
|------|---------|
| `search_transcripts` | Semantic + keyword search |
| `search_by_speaker` | Filter by who said it |
| `search_by_date_range` | Filter by recording date |
| `get_entity_info` | Entity details + relationships |
| `get_video_transcript` | Full transcript of one video |
| `get_segment_context` | Expand context around a segment |
| `list_videos` | Browse available videos |
| `get_topic_timeline` | Chronological view of topic |

**Dependencies**: Requires Phase 3 for entity and speaker data.

---

## Phase 5: Knowledge Graph & Curation

**Goal**: Neo4j integration and user curation capabilities

### K1: Evolving Knowledge Graph
- **As** the system
- **I want to** maintain an evolving knowledge graph
- **So that** the domain model improves as videos are added
- **Acceptance Criteria:**
  - New videos update/extend existing knowledge
  - Concepts linked across videos
  - Graph structure reflects domain relationships

### K2: Knowledge Graph Visualization
- **As a** Knowledge Seeker
- **I want to** browse the knowledge graph visually
- **So that** I can explore domain concepts and their relationships
- **Acceptance Criteria:**
  - Visual representation of topics/entities
  - Clickable nodes lead to related content
  - Shows which videos discuss each concept

### K3: Topic Timeline
- **As a** Knowledge Seeker
- **I want to** see a timeline of a specific topic
- **So that** I can understand how it evolved over time
- **Acceptance Criteria:**
  - Select topic to see chronological view
  - Shows when topic was discussed
  - Indicates if information was superseded

### K4: Content Currency Detection
- **As** the system
- **I want to** identify when new content contradicts or supersedes older content
- **So that** users understand currency
- **Acceptance Criteria:**
  - Flag potential conflicts/updates
  - Suggest relationships: "This may update information from [earlier video]"

### S5: Temporal Queries
- **As a** Knowledge Seeker
- **I want to** ask date-related questions
- **So that** I can find when things happened
- **Acceptance Criteria:**
  - "When was feature X added?"
  - "What problems were discussed in Q3 2024?"
  - Temporal queries understood

### U1: Transcript Editing
- **As a** Curator
- **I want to** edit transcription text
- **So that** I can correct AI errors (especially technical terms and names)
- **Acceptance Criteria:**
  - Editable transcript view
  - Changes saved and reflected in search index
  - Edit history preserved

### U2: Timestamped Comments
- **As a** Knowledge Seeker
- **I want to** add timestamped comments on videos
- **So that** I can annotate insights or context
- **Acceptance Criteria:**
  - Comment input tied to current timestamp
  - Comments visible on video timeline
  - Comments searchable

### U3: Content Deprecation
- **As a** Curator
- **I want to** mark content as outdated/superseded
- **So that** seekers know to look for newer information
- **Acceptance Criteria:**
  - Deprecation flag on segments
  - Optional link to superseding content
  - Visual indicator in search results

### U4: Entity Correction
- **As a** Curator
- **I want to** correct or enhance entity extraction
- **So that** the knowledge graph is accurate
- **Acceptance Criteria:**
  - Review extracted entities
  - Merge duplicates, fix misidentifications
  - Add entities AI missed

---

## Phase 6: Polish & Administration

**Goal**: Complete video management, system configuration, and UX refinement

### M2: Metadata Editing
- **As a** Content Admin
- **I want to** update video metadata after upload
- **So that** I can correct mistakes or add information
- **Acceptance Criteria:**
  - Edit title, date, participants, notes
  - Re-index if needed

### M3: Video Deletion
- **As a** Content Admin
- **I want to** delete videos
- **So that** I can remove content that's no longer relevant
- **Acceptance Criteria:**
  - Delete with confirmation
  - Removes from search index and knowledge graph
  - Handles orphaned references

### M4: System Settings
- **As a** Content Admin
- **I want to** configure system processing options
- **So that** I can optimize quality vs cost tradeoffs for my use case
- **Acceptance Criteria:**
  - Settings page accessible from main navigation
  - Configurable options include:
    - Chunking strategy (embedding-based, LLM-based, or both)
    - Entity extraction toggle and model selection
    - Transcription settings (Whisper model, language)
    - Search settings (default mode, hybrid search weight)
  - Cost indicators shown for LLM-based features
  - Settings apply to newly processed videos
  - Option to reprocess existing videos with new settings

---

## Phase 7: Conversation Persistence

**Goal**: Save and resume conversation sessions

### C1: Conversation History
- **As a** Knowledge Seeker
- **I want** my conversation history saved
- **So that** I can return and continue where I left off
- **Acceptance Criteria:**
  - Conversations persisted across sessions
  - List of previous conversations
  - Resume any conversation

### C2: Conversation Organization
- **As a** Knowledge Seeker
- **I want to** name/organize my saved conversations
- **So that** I can find them later
- **Acceptance Criteria:**
  - Rename conversations
  - Delete old conversations
  - Search conversation history

---

## Coverage Verification

### All User Stories by Epic

| Epic | Stories | Phases |
|------|---------|--------|
| Video Ingestion (V) | V1, V2, V3, V4 | 1, 2 |
| Intelligent Analysis (A) | A1, A2, A3, A4 | 3 |
| Knowledge Graph (K) | K1, K2, K3, K4 | 5 |
| Search & Discovery (S) | S1, S2, S3, S4, S5, S6, S7, S8, S9, S10 | 1, 2, 3, 5 |
| Playback (P) | P1, P2, P3, P4 | 1, 3 |
| User Annotations (U) | U1, U2, U3, U4 | 5 |
| Management (M) | M1, M2, M3, M4 | 1, 6 |
| Conversation (C) | C1, C2 | 7 |

### Stories Per Phase

```
Phase 1: V1, V2, V3, P1, P2, P3, S1, S3, M1           (9 stories)
Phase 2: S7, S8, S9, S2, S10, V4                       (6 stories)
Phase 3: A1, A2, A3, A4, S4, S6, P4                    (7 stories)
Phase 4: (infrastructure only)                          (0 stories)
Phase 5: K1, K2, K3, K4, S5, U1, U2, U3, U4            (9 stories)
Phase 6: M2, M3, M4                                     (3 stories)
Phase 7: C1, C2                                         (2 stories)
                                                       ─────────────
                                                        36 stories
```

All 36 user stories are accounted for.
