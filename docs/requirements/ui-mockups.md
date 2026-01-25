# UI Mockups

This document contains wireframe specifications for the Whedifaqaui frontend interface.

## Application Structure

The application consists of three primary views:
1. **Search View** - Main workspace for asking questions and viewing content
2. **Library View** - Video management and upload
3. **Settings View** - System configuration and feature toggles

## Main Application Layout (Search View)

The search view uses a three-panel layout optimized for conversational search:

```
+===========================================================================+
|  WHEDIFAQAUI                                              [Video Library] |
+===========================================================================+
|                    |                      |                               |
|    CONVERSATION    |     RESULTS LIST     |         CONTENT PANE          |
|      (Panel 1)     |      (Panel 2)       |          (Panel 3)            |
|                    |                      |                               |
+--------------------+----------------------+-------------------------------+
```

### Panel Descriptions

| Panel | Purpose | Behavior |
|-------|---------|----------|
| **Conversation** | Chat-style Q&A with AI | Scrolls vertically, input at bottom |
| **Results List** | Accumulated search findings | Scrollable list, selection highlights |
| **Content Pane** | Display selected content | Shows video player or document |

### Detailed Search View

```
+===========================================================================+
|  WHEDIFAQAUI                                              [Video Library] |
+===========================================================================+
|                    |                      |                               |
|    CONVERSATION    |     RESULTS LIST     |         CONTENT PANE          |
|                    |                      |                               |
|  +--------------+  |  +----------------+  |  +-------------------------+  |
|  | USER         |  |  |                |  |  |                         |  |
|  | What was     |  |  | [Selected]     |  |  |    +---------------+    |  |
|  | discussed    |  |  | > Video 1      |  |  |    |               |    |  |
|  | about AWS    |  |  |   @ 12:34      |  |  |    |  VIDEO        |    |  |
|  | Cognito?     |  |  |   "Setting up  |  |  |    |  PLAYER       |    |  |
|  +--------------+  |  |    user pools" |  |  |    |               |    |  |
|                    |  +----------------+  |  |    +---------------+    |  |
|  +--------------+  |  +----------------+  |  |    [<] 12:34 [>] [|||]  |  |
|  | AI           |  |  |                |  |  |                         |  |
|  | I found 3    |  |  |   Video 3      |  |  |  TRANSCRIPT             |  |
|  | discussions  |  |  |   @ 45:12      |  |  |  +-----------------------+|
|  | about AWS    |  |  |   "Cognito     |  |  |  | ...and then we       ||
|  | Cognito:     |  |  |    triggers"   |  |  |  | configured the       ||
|  |              |  |  +----------------+  |  |  | [user pool] to use   ||
|  | 1. Setting   |  |  +----------------+  |  |  | email verification   ||
|  |    up user   |  |  |                |  |  |  | which solved the...  ||
|  |    pools     |  |  |   Video 7      |  |  |  +-----------------------+|
|  | 2. Lambda    |  |  |   @ 03:22      |  |  |                         |  |
|  |    triggers  |  |  |   "Migration   |  |  |  [Add Comment]          |  |
|  | 3. Migration |  |  |    from Auth0" |  |  |                         |  |
|  |    from      |  |  +----------------+  |  +-------------------------+  |
|  |    Auth0     |  |                      |                               |
|  +--------------+  |                      |                               |
|                    |  +----------------+  |                               |
|  +--------------+  |  |                |  |                               |
|  | USER         |  |  |  [Document]    |  |                               |
|  | Summarize    |  |  |   Summary of   |  |                               |
|  | the first    |  |  |   Cognito      |  |                               |
|  | video        |  |  |   Setup        |  |                               |
|  +--------------+  |  +----------------+  |                               |
|                    |                      |                               |
|  +--------------+  |                      |                               |
|  | AI           |  |                      |                               |
|  | Here's a     |  |                      |                               |
|  | summary...   |  |                      |                               |
|  | [Document    |  |                      |                               |
|  |  added to    |  |                      |                               |
|  |  results]    |  |                      |                               |
|  +--------------+  |                      |                               |
|                    |                      |                               |
| +----------------+ |                      |                               |
| | Ask a question | |                      |                               |
| | ...            | |                      |                               |
| +----------------+ |                      |                               |
+--------------------+----------------------+-------------------------------+
```

### Conversation Panel Components

```
+----------------------+
|   CONVERSATION       |
+----------------------+
|                      |
| +------------------+ |
| | USER             | |  <- User message bubble
| | [question text]  | |     Right-aligned or distinct color
| +------------------+ |
|                      |
| +------------------+ |
| | AI               | |  <- AI response bubble
| | [response text]  | |     Left-aligned or distinct color
| | [citations]      | |     Includes inline citations
| +------------------+ |
|                      |
| [... more messages]  |
|                      |
+----------------------+
| +------------------+ |
| | Ask a question.. | |  <- Text input field
| +------------------+ |
| [Send button]        |
+----------------------+
```

### Results List Components

```
+----------------------+
|    RESULTS LIST      |
+----------------------+
|                      |
| +------------------+ |
| | [Video icon]     | |  <- Video result item
| | Video Title      | |
| | @ HH:MM:SS       | |     Timestamp
| | "Preview text.." | |     Brief excerpt
| +------------------+ |
|                      |
| +------------------+ |
| | [Doc icon]       | |  <- Document result item
| | Document Title   | |
| | Generated        | |     Type indicator
| +------------------+ |
|                      |
+----------------------+
```

### Result Item States

| State | Visual Indicator |
|-------|------------------|
| Default | Standard styling |
| Hover | Highlight background |
| Selected | Bold border, distinct background |
| Video | Film/play icon |
| Document | Document/file icon |

---

## Content Pane: Video View

When a video result is selected:

```
+-------------------------------+
|         CONTENT PANE          |
+-------------------------------+
|                               |
|    +---------------------+    |
|    |                     |    |
|    |    VIDEO PLAYER     |    |  <- Embedded video player
|    |                     |    |
|    +---------------------+    |
|    [<<] [>] [>>]  12:34/45:00 |  <- Playback controls
|    [---|------o----------|]   |  <- Seek bar
|    [Volume] [Fullscreen]      |
|                               |
+-------------------------------+
|  TRANSCRIPT                   |
|  +---------------------------+|
|  | [12:30] Previous segment  ||  <- Clickable segments
|  |                           ||
|  | [12:34] **Current segment || <- Highlighted current
|  | being spoken right now    ||
|  |                           ||
|  | [12:45] Next segment      ||
|  +---------------------------+|
|                               |
|  [Add Comment at 12:34]       |  <- Comment input
+-------------------------------+
```

---

## Content Pane: Document View

When a generated document is selected:

```
+-------------------------------+
|         CONTENT PANE          |
+-------------------------------+
|                               |
|  DOCUMENT VIEWER              |
|  +---------------------------+|
|  |                           ||
|  | # Summary: AWS Cognito    ||  <- Markdown rendered
|  |   Setup                   ||
|  |                           ||
|  | ## Overview               ||
|  | The team configured       ||
|  | AWS Cognito for user      ||
|  | authentication with       ||
|  | the following setup...    ||
|  |                           ||
|  | ## Key Decisions          ||
|  | - Email verification      ||
|  |   enabled                 ||
|  | - Custom Lambda for       ||
|  |   post-confirmation       ||
|  |                           ||
|  | ## Sources                ||
|  | - Video 1 @ 12:34 [link]  ||  <- Clickable source links
|  | - Video 3 @ 45:12 [link]  ||
|  |                           ||
|  +---------------------------+|
|                               |
|  [Download as PDF] [Copy]     |  <- Export options
|                               |
+-------------------------------+
```

---

## Video Library View

```
+===========================================================================+
|  WHEDIFAQAUI                                                    [Search]  |
+===========================================================================+
|                                                                           |
|  VIDEO LIBRARY                                          [+ Upload Video]  |
|                                                                           |
|  +-----------+  +--------------+  +------------------+                    |
|  | Status: v |  | Date Range:v |  | Sort: Newest 1st |                    |
|  +-----------+  +--------------+  +------------------+                    |
|                                                                           |
|  +---------------------------------------------------------------------+  |
|  | +-------+                                                           |  |
|  | | [>]   |  Sprint 42 Planning Session                     Ready    |  |
|  | | thumb |  Dec 15, 2024  |  1h 23m  |  John, Sarah, Mike            |  |
|  | +-------+  "Discussed Q1 roadmap and technical debt priorities"     |  |
|  |                                                    [Edit] [Delete]  |  |
|  +---------------------------------------------------------------------+  |
|                                                                           |
|  +---------------------------------------------------------------------+  |
|  | +-------+                                                           |  |
|  | | [>]   |  Authentication System Deep Dive                Ready    |  |
|  | | thumb |  Dec 10, 2024  |  45m  |  Sarah                           |  |
|  | +-------+  "Complete walkthrough of Cognito setup and flows"        |  |
|  |                                                    [Edit] [Delete]  |  |
|  +---------------------------------------------------------------------+  |
|                                                                           |
|  +---------------------------------------------------------------------+  |
|  | +-------+                                                           |  |
|  | | [...]  |  Database Migration Walkthrough            Processing   |  |
|  | | thumb |  Dec 8, 2024  |  2h 05m  |  Mike, John                    |  |
|  | +-------+  "Migration from PostgreSQL to Aurora"                    |  |
|  |                                      [=====>        ] 45%           |  |
|  +---------------------------------------------------------------------+  |
|                                                                           |
|  +---------------------------------------------------------------------+  |
|  | +-------+                                                           |  |
|  | | [...]  |  API Gateway Configuration                 Transcribing  |  |
|  | | thumb |  Dec 5, 2024  |  38m  |  Sarah                            |  |
|  | +-------+                                                           |  |
|  |                                      [===>          ] 25%           |  |
|  +---------------------------------------------------------------------+  |
|                                                                           |
|  Showing 4 of 12 videos                                    [Load More]    |
|                                                                           |
+===========================================================================+
```

### Video Card Components

| Element | Description |
|---------|-------------|
| Thumbnail | Preview image or placeholder |
| Title | Video name |
| Status badge | Ready / Processing / Transcribing / Error |
| Date | Recording date |
| Duration | Video length |
| Participants | List of speakers |
| Context notes | Brief description |
| Progress bar | Shown during processing |
| Actions | Edit, Delete buttons |

### Status Indicators

| Status | Visual |
|--------|--------|
| Ready | Green badge, play icon |
| Processing | Yellow badge, spinner |
| Transcribing | Blue badge, text icon |
| Analyzing | Purple badge, brain icon |
| Error | Red badge, warning icon |

---

## Video Upload Modal

```
+--------------------------------------------------+
|  UPLOAD VIDEO                              [X]   |
+--------------------------------------------------+
|                                                  |
|  +--------------------------------------------+  |
|  |                                            |  |
|  |        +------------------+                |  |
|  |        |   [File Icon]    |                |  |
|  |        +------------------+                |  |
|  |                                            |  |
|  |     Drag and drop MKV file here            |  |
|  |              or                            |  |
|  |         [Browse Files]                     |  |
|  |                                            |  |
|  +--------------------------------------------+  |
|                                                  |
|  Title *                                         |
|  +--------------------------------------------+  |
|  | Sprint 42 Planning Session                 |  |
|  +--------------------------------------------+  |
|                                                  |
|  Recording Date *                                |
|  +--------------------------------------------+  |
|  | 2024-12-15                          [Cal]  |  |
|  +--------------------------------------------+  |
|                                                  |
|  Participants (optional)                         |
|  +--------------------------------------------+  |
|  | John Smith, Sarah Jones, Mike Chen         |  |
|  +--------------------------------------------+  |
|  Separate names with commas                      |
|                                                  |
|  Context Notes (optional)                        |
|  +--------------------------------------------+  |
|  | Discussed Q1 roadmap priorities and        |  |
|  | technical debt items. Key decisions about  |  |
|  | authentication migration timeline.          |  |
|  |                                            |  |
|  +--------------------------------------------+  |
|                                                  |
|                        [Cancel]  [Upload Video]  |
+--------------------------------------------------+
```

### Upload Form Validation

| Field | Validation |
|-------|------------|
| File | Required, must be MKV format |
| Title | Required, max 200 characters |
| Recording Date | Required, valid date format |
| Participants | Optional, comma-separated |
| Context Notes | Optional, max 2000 characters |

### Upload States

```
+--------------------------------------------------+
|  UPLOADING...                              [X]   |
+--------------------------------------------------+
|                                                  |
|  Sprint 42 Planning Session.mkv                  |
|                                                  |
|  [=========================>          ] 65%      |
|                                                  |
|  Uploading: 156 MB / 240 MB                      |
|                                                  |
|                                        [Cancel]  |
+--------------------------------------------------+
```

---

## Knowledge Graph View (Phase 4)

```
+===========================================================================+
|  WHEDIFAQAUI                                              [Video Library] |
+===========================================================================+
|                                                                           |
|  KNOWLEDGE GRAPH                                         [Search] [List]  |
|                                                                           |
|  +---------------------------------------------------------------------+  |
|  |                                                                     |  |
|  |                    +----------------+                               |  |
|  |                    | Authentication |                               |  |
|  |                    |    (8 refs)    |                               |  |
|  |                    +-------+--------+                               |  |
|  |                            |                                        |  |
|  |              +-------------+-------------+                          |  |
|  |              |                           |                          |  |
|  |     +--------+--------+        +---------+---------+                |  |
|  |     |  AWS Cognito    |        |     Auth0         |                |  |
|  |     |    (5 refs)     |--------|    (3 refs)       |                |  |
|  |     +--------+--------+  migrated  +---------------+                |  |
|  |              |            from                                      |  |
|  |     +--------+--------+                                             |  |
|  |     |                 |                                             |  |
|  | +---+----+    +-------+-------+                                     |  |
|  | | User   |    | Lambda        |                                     |  |
|  | | Pools  |    | Triggers      |                                     |  |
|  | |(3 refs)|    | (2 refs)      |                                     |  |
|  | +--------+    +---------------+                                     |  |
|  |                                                                     |  |
|  +---------------------------------------------------------------------+  |
|                                                                           |
|  SELECTED: AWS Cognito                                                    |
|  +---------------------------------------------------------------------+  |
|  | Related Videos:                                                     |  |
|  | - Authentication System Deep Dive (Dec 10) - 5 mentions             |  |
|  | - Sprint 42 Planning (Dec 15) - 2 mentions                          |  |
|  |                                                                     |  |
|  | Timeline: First discussed Oct 5, most recent Dec 15                 |  |
|  |                                                                     |  |
|  | Related Concepts: User Pools, Lambda Triggers, Auth0                |  |
|  +---------------------------------------------------------------------+  |
|                                                                           |
+===========================================================================+
```

### Graph Interaction

| Action | Result |
|--------|--------|
| Click node | Select node, show details panel |
| Double-click node | Navigate to search filtered by entity |
| Drag node | Reposition in graph |
| Scroll | Zoom in/out |
| Click edge | Show relationship details |

### Node Visual Encoding

| Element | Encoding |
|---------|----------|
| Size | Number of references |
| Color | Entity type (person, system, concept) |
| Border | Recency (recent = solid, old = dashed) |
| Badge | Deprecated indicator |

---

## System Settings View

```
+===========================================================================+
|  WHEDIFAQAUI                                              [Video Library] |
+===========================================================================+
|                                                                           |
|  SYSTEM SETTINGS                                                          |
|                                                                           |
|  +---------------------------------------------------------------------+  |
|  |  PROCESSING PIPELINE                                                |  |
|  +---------------------------------------------------------------------+  |
|  |                                                                     |  |
|  |  Chunking Strategy                                                  |  |
|  |  +---------------------------------------------------------------+  |  |
|  |  | ( ) Embedding-based    - Fast, local, good quality            |  |  |
|  |  | ( ) LLM-based          - Better quality, costs ~$0.002/video  |  |  |
|  |  | (•) Both (comparison)  - Run both, compare results            |  |  |
|  |  +---------------------------------------------------------------+  |  |
|  |                                                                     |  |
|  |  Embedding Chunking Settings              [Collapsed v]             |  |
|  |  +---------------------------------------------------------------+  |  |
|  |  | Similarity Threshold     [====o====] 0.5                      |  |  |
|  |  | Min Chunk Tokens         [  100  ]                            |  |  |
|  |  | Max Chunk Tokens         [  500  ]                            |  |  |
|  |  +---------------------------------------------------------------+  |  |
|  |                                                                     |  |
|  |  LLM Chunking Settings                    [Collapsed v]             |  |
|  |  +---------------------------------------------------------------+  |  |
|  |  | Include Chunk Summaries  [x]                                  |  |  |
|  |  | LLM Model               [Claude Haiku v]                      |  |  |
|  |  +---------------------------------------------------------------+  |  |
|  |                                                                     |  |
|  +---------------------------------------------------------------------+  |
|                                                                           |
|  +---------------------------------------------------------------------+  |
|  |  CONTENT ANALYSIS                                                   |  |
|  +---------------------------------------------------------------------+  |
|  |                                                                     |  |
|  |  Entity Extraction                                                  |  |
|  |  +---------------------------------------------------------------+  |  |
|  |  | Enable Entity Extraction [x]                                  |  |  |
|  |  | LLM Model               [Claude Haiku v]                      |  |  |
|  |  | Extract Relationships   [x]                                   |  |  |
|  |  +---------------------------------------------------------------+  |  |
|  |                                                                     |  |
|  |  Chunk Summaries (for search)                                       |  |
|  |  +---------------------------------------------------------------+  |  |
|  |  | Generate Summaries      [ ]  - Adds ~$0.01/video              |  |  |
|  |  | Embed Summaries         [ ]  - Enables concept-level search   |  |  |
|  |  +---------------------------------------------------------------+  |  |
|  |                                                                     |  |
|  +---------------------------------------------------------------------+  |
|                                                                           |
|  +---------------------------------------------------------------------+  |
|  |  TRANSCRIPTION                                                      |  |
|  +---------------------------------------------------------------------+  |
|  |                                                                     |  |
|  |  Whisper Settings                                                   |  |
|  |  +---------------------------------------------------------------+  |  |
|  |  | Model                   [large-v2 v]                          |  |  |
|  |  | Language                [English v]                           |  |  |
|  |  | Device                  [GPU (CUDA) v]                        |  |  |
|  |  +---------------------------------------------------------------+  |  |
|  |                                                                     |  |
|  |  Speaker Diarization (Phase 3)                                      |  |
|  |  +---------------------------------------------------------------+  |  |
|  |  | Enable Speaker ID       [x]                                   |  |  |
|  |  +---------------------------------------------------------------+  |  |
|  |                                                                     |  |
|  +---------------------------------------------------------------------+  |
|                                                                           |
|  +---------------------------------------------------------------------+  |
|  |  SEARCH & QUERY                                                     |  |
|  +---------------------------------------------------------------------+  |
|  |                                                                     |  |
|  |  Query Modes                                                        |  |
|  |  +---------------------------------------------------------------+  |  |
|  |  | Default Mode            [Quick Mode v]                        |  |  |
|  |  | Enable Deep Mode        [x]  (Phase 4)                        |  |  |
|  |  +---------------------------------------------------------------+  |  |
|  |                                                                     |  |
|  |  Search Settings                                                    |  |
|  |  +---------------------------------------------------------------+  |  |
|  |  | Results per Query       [  10  ]                              |  |  |
|  |  | Hybrid Search Weight    BM25 [===o===] Vector                 |  |  |
|  |  +---------------------------------------------------------------+  |  |
|  |                                                                     |  |
|  +---------------------------------------------------------------------+  |
|                                                                           |
|                                          [Reset to Defaults] [Save]       |
|                                                                           |
+===========================================================================+
```

### Settings Categories

| Category | Settings |
|----------|----------|
| **Processing Pipeline** | Chunking strategy, embedding params, LLM params |
| **Content Analysis** | Entity extraction, summaries, relationships |
| **Transcription** | Whisper model, language, speaker diarization |
| **Search & Query** | Query modes, hybrid search weights |

### Settings Persistence

| Aspect | Behavior |
|--------|----------|
| Storage | PostgreSQL `system_settings` table |
| Scope | System-wide (not per-user) |
| Changes | Applied to new videos only |
| Reprocessing | Option to reprocess existing videos with new settings |

### Cost Indicators

Settings with cost implications show estimates:
- LLM-based chunking: ~$0.002/video
- Generate Summaries: ~$0.01/video
- Entity Extraction: ~$0.005/video

---

## Target Platform

**Desktop only** (1200px+ viewport)
- Full three-panel layout
- All panels visible simultaneously
- Optimized for mouse/keyboard interaction

---

## Accessibility Requirements

| Requirement | Implementation |
|-------------|----------------|
| Keyboard navigation | All interactive elements focusable |
| Screen reader | ARIA labels on all components |
| Color contrast | WCAG AA minimum |
| Video captions | Transcript serves as captions |
| Focus indicators | Visible focus states |
