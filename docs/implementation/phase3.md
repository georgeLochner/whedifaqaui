# Phase 3: High-Level Architectural Plan

**Phase**: Intelligent Analysis
**Goal**: Enrich content understanding through entity extraction, visual analysis, and speaker features.

---

## Phase 3 Scope

| Story | Description |
|-------|-------------|
| A1 | Visual Content Capture - Critical frame extraction and Claude descriptions |
| A2 | Speaker Display - Auto-infer names for UI display only (not searchable) |
| A3 | Entity Extraction - Extract people, projects, systems, dates from content |
| A4 | Topic Understanding - Deep content analysis, concept extraction |
| S4 | Entity Search - Search by specific entities ("everything about Cognito") |
| S6 | Fuzzy Matching - Handle typos and spelling variations |
| P4 | Visual Content Display - Show screenshots in video timeline |

**Key Design Decisions:**
- **File references** - pass file paths to Claude, not large text in prompts
- **Pipe-delimited output** - reliable parsing (not JSON, which Claude produces inconsistently)
- **Single Claude call** analyzes entire transcript → entities, relationships, speaker mapping, critical frames
- **Critical frames only** - Claude identifies important visual moments (max 10 per video)
- **No OCR library** - Claude reads image files directly and extracts text
- **Speaker names are display-only** - not indexed for search (see rationale below)

### Speaker Naming: Display Only (Not Searchable)

Speaker names are mapped for **UI readability only**, not for search:

| What | Indexed? | Purpose |
|------|----------|---------|
| `segments.speaker` (SPEAKER_00) | YES | Basic attribution |
| `speaker_mappings.speaker_name` | NO | Display in UI |
| Search by speaker name | NO | Use entity search instead |

**Rationale:**
- Cross-video speaker identity is complex (same person = different labels)
- Name variations need canonicalization ("John" vs "John Smith")
- Entity search handles "find mentions of John" better (finds discussions ABOUT John too)
- Complexity not worth the limited search value

**For people search, use entities instead:**
```
User: "What did John talk about?"
→ Search entities: type=person, name=John
→ Returns segments where John is mentioned (as entity)
```

---

## Architecture: Extended Processing Pipeline

Phase 3 adds a unified content analysis stage using Claude:

```
Phase 1 Pipeline:
UPLOAD → VIDEO_PROCESSING → TRANSCRIPTION (WhisperX) → CHUNKING → INDEXING → READY
                                  │
                                  └── Speaker labels (SPEAKER_00, SPEAKER_01)

Phase 3 Pipeline (extended):
UPLOAD → VIDEO_PROCESSING → TRANSCRIPTION → CHUNKING
                                               │
                                               ▼
                                    ┌─────────────────────┐
                                    │  CONTENT_ANALYSIS   │
                                    │  (Single Claude call)│
                                    │                     │
                                    │  Returns:           │
                                    │  • Entities         │
                                    │  • Relationships    │
                                    │  • Speaker mapping  │
                                    │  • Critical frames  │
                                    └──────────┬──────────┘
                                               │
                                               ▼
                                    ┌─────────────────────┐
                                    │  FRAME_EXTRACTION   │
                                    │  (FFmpeg)           │
                                    │                     │
                                    │  Only timestamps    │
                                    │  from Claude output │
                                    │  (max 10 frames)    │
                                    └──────────┬──────────┘
                                               │
                                               ▼
                                    ┌─────────────────────┐
                                    │  FRAME_DESCRIPTION  │
                                    │  (Claude per frame) │
                                    │                     │
                                    │  Visual description │
                                    │  + text extraction  │
                                    └──────────┬──────────┘
                                               │
                                               ▼
                                           INDEXING → READY
```

---

## Project Structure Changes (Phase 3 Additions)

```
backend/
├── app/
│   ├── api/
│   │   └── routes/
│   │       ├── entities.py         # NEW: S4 - Entity search/browse
│   │       ├── speakers.py         # NEW: A2 - Speaker endpoints
│   │       └── screenshots.py      # NEW: P4 - Screenshot endpoints
│   │
│   ├── services/
│   │   ├── content_analysis.py     # NEW: A3, A4, A2, A1 - Unified Claude analysis
│   │   ├── entity.py               # NEW: A3 - Entity CRUD & normalization
│   │   ├── speaker.py              # NEW: A2 - Speaker mapping management
│   │   ├── screenshot.py           # NEW: A1 - Screenshot extraction & description
│   │   └── search.py               # MODIFIED: S4, S6 - Entity/speaker filters, fuzzy
│   │
│   ├── tasks/
│   │   ├── content_analysis.py     # NEW: Single Claude call for all analysis
│   │   ├── frame_extraction.py     # NEW: FFmpeg extract critical frames
│   │   └── frame_description.py    # NEW: Claude describe each frame
│   │
│   ├── models/
│   │   ├── entity.py               # NEW: A3 - Entity model
│   │   ├── entity_mention.py       # NEW: A3 - Entity-segment links
│   │   ├── entity_relationship.py  # NEW: A3 - Entity relationships
│   │   ├── topic.py                # NEW: A4 - Topic model
│   │   ├── screenshot.py           # NEW: A1 - Screenshot model
│   │   └── speaker_mapping.py      # NEW: A2 - Map SPEAKER_00 → "John"
│   │
│   └── schemas/
│       ├── entity.py               # NEW: Entity schemas
│       ├── speaker.py              # NEW: Speaker schemas
│       └── screenshot.py           # NEW: Screenshot schemas

frontend/
├── src/
│   ├── pages/
│   │   └── EntityPage.tsx          # NEW: S4 - Entity detail view
│   │
│   ├── components/
│   │   ├── entities/               # NEW: Entity components
│   │   │   ├── EntityCard.tsx      # Entity display card
│   │   │   ├── EntityList.tsx      # Filterable entity list
│   │   │   └── EntityMentions.tsx  # Timeline of mentions
│   │   │
│   │   ├── speakers/               # NEW: Speaker components (display only)
│   │   │   ├── SpeakerBadge.tsx    # Speaker name in transcript
│   │   │   └── SpeakerMappingModal.tsx  # A2: Override name mappings
│   │   │
│   │   ├── visual/                 # NEW: Visual content components
│   │   │   ├── ScreenshotGallery.tsx   # P4: Screenshots in timeline
│   │   │   ├── ScreenshotCard.tsx      # Single screenshot display
│   │   │   └── ScreenshotViewer.tsx    # Full-size viewer
│   │   │
│   │   └── search/
│   │       ├── EntityFilter.tsx    # NEW: S4 - Entity filter chips
│   │       └── SearchBar.tsx       # MODIFIED: S6 - Fuzzy suggestions
│   │
│   ├── api/
│   │   ├── entities.ts             # NEW: Entity API client
│   │   └── speakers.ts             # NEW: Speaker API client
│   │
│   └── types/
│       ├── entity.ts               # NEW: Entity types
│       ├── speaker.ts              # NEW: Speaker types
│       └── screenshot.ts           # NEW: Screenshot types

data/
├── videos/
│   └── screenshots/                # NEW: Extracted screenshots
│       └── {video_id}/
│           ├── 00125.jpg           # Screenshot at 125 seconds
│           └── 00340.jpg           # Screenshot at 340 seconds
```

---

## Component Specification by Layer

### Backend: New Processing Tasks

| Task | Technology | Purpose |
|------|------------|---------|
| `content_analysis` | Claude CLI | Single call: entities, relationships, speaker mapping, critical frames |
| `frame_extraction` | FFmpeg | Extract only the critical frames identified by Claude |
| `frame_description` | Claude CLI | Describe each frame (visual content + text extraction) |

**Key Design Decisions:**
- One Claude call analyzes entire transcript (better context for entity disambiguation)
- Claude identifies speaker names from context ("as John mentioned earlier...")
- Claude identifies critical visual moments (max 10 per video, configurable)
- No OCR library - Claude extracts text from frame images directly

### Backend: New API Routes

| Route | Method | Purpose | Stories |
|-------|--------|---------|---------|
| `/api/entities` | GET | List all entities (filterable by type) | S4 |
| `/api/entities/{id}` | GET | Entity detail with all mentions | S4 |
| `/api/entities/search` | GET | Search entities by name (fuzzy) | S4, S6 |
| `/api/videos/{id}/speakers` | GET | Get speaker mappings for video (display only) | A2 |
| `/api/videos/{id}/speakers` | PUT | Override/correct speaker mapping | A2 |
| `/api/videos/{id}/screenshots` | GET | Get screenshots for a video | P4 |
| `/api/search` | GET | MODIFIED: Add entity filter, fuzzy matching | S4, S6 |

Note: Search does NOT filter by speaker name. Use entity search for people.

### Backend: New Services

| Service | Responsibility |
|---------|----------------|
| `content_analysis.py` | Orchestrate Claude analysis, parse unified response |
| `entity.py` | Entity CRUD, normalization, relationship management |
| `speaker.py` | Speaker mapping storage and lookup |
| `screenshot.py` | Frame extraction (FFmpeg) and description (Claude) |

### Backend: New/Modified Models

| Model | Type | Key Fields |
|-------|------|------------|
| `Entity` | NEW | id, name, canonical_name, type, description, aliases[], mention_count |
| `EntityMention` | NEW | id, entity_id, segment_id, video_id, timestamp, confidence |
| `EntityRelationship` | NEW | id, source_entity_id, target_entity_id, relation_type, video_id |
| `Topic` | NEW | id, name, description, parent_topic_id |
| `TopicMention` | NEW | id, topic_id, segment_id, video_id, timestamp |
| `Screenshot` | NEW | id, video_id, timestamp, file_path, ocr_text, description |
| `SpeakerMapping` | NEW | id, video_id, speaker_label, speaker_name |

### Frontend: New Pages

| Page | Route | Stories |
|------|-------|---------|
| `EntityPage` | `/entities/:id` | S4 - Entity detail with mentions |

### Frontend: New Component Groups

| Group | Components | Purpose |
|-------|------------|---------|
| `entities/` | EntityCard, EntityList, EntityMentions | Entity display and navigation |
| `speakers/` | SpeakerBadge, SpeakerMappingModal | Speaker name display (not searchable) |
| `visual/` | ScreenshotGallery, ScreenshotCard, ScreenshotViewer | Visual content display |

---

## Claude Output Format

### Why Pipe-Delimited (Not JSON)?

Claude does not reliably produce valid JSON:
- Trailing commas, comments, unquoted keys
- Preamble text before JSON
- Truncation on long outputs

Pipe-delimited format is:
- Simple to produce
- Trivial to parse
- No syntax errors possible
- Easy to validate

### Format Specification

```
TYPE|FIELD1|FIELD2|FIELD3...
```

| Record Type | Fields | Example |
|-------------|--------|---------|
| `ENTITY` | name, type, description | `ENTITY\|AWS Cognito\|system\|Auth service` |
| `REL` | source, relation, target, timestamp | `REL\|Cognito\|replaced\|Auth0\|125` |
| `SPEAKER` | label, name, confidence | `SPEAKER\|SPEAKER_00\|John\|0.9` |
| `FRAME` | timestamp, reason | `FRAME\|15\|Architecture diagram shown` |
| `TOPIC` | name | `TOPIC\|authentication` |
| `CONTENT_TYPE` | type | `CONTENT_TYPE\|diagram` |
| `TEXT` | extracted text | `TEXT\|API Gateway → Auth` |
| `DESC` | description | `DESC\|Three-tier architecture` |
| `DETAIL` | technical detail | `DETAIL\|microservices` |

### Rules

- One record per line
- Fields separated by `|`
- First field = record type
- Lines starting with `#` = comments (ignored)
- Empty lines ignored

---

## Processing Pipeline Details

### Step 1: Content Analysis (Single Claude Call)

One Claude call analyzes the entire transcript via **file reference** (not inline text):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  CONTENT ANALYSIS TASK                                                       │
│                                                                              │
│  Transcript file (already exists from Phase 1):                             │
│  /data/transcripts/{video_id}.json                                          │
│                                                                              │
│  Contains:                                                                  │
│  {                                                                          │
│    "video_id": "vid-123",                                                  │
│    "whisper_segments": [                                                    │
│      {"start": 0, "end": 8, "text": "We need to discuss...", "speaker": "SPEAKER_00"},
│      {"start": 8, "end": 15, "text": "I agree, John...", "speaker": "SPEAKER_01"}
│    ]                                                                        │
│  }                                                                          │
│                                                                              │
│  Prompt (small, references file):                                           │
│  "READ FILE: /data/transcripts/vid-123.json                                │
│   Participants: John Smith, Sarah Chen                                      │
│   Max critical frames: 10                                                   │
│   ..."                                                                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  PROMPT SENT TO CLAUDE (file reference + output format specification)       │
│                                                                              │
│  """                                                                        │
│  Analyze the video transcript for content extraction.                       │
│                                                                              │
│  READ THIS FILE: /data/transcripts/vid-123.json                            │
│                                                                              │
│  Video metadata:                                                            │
│  - Title: Auth Migration Meeting                                            │
│  - Participants: John Smith, Sarah Chen                                     │
│  - Recording date: 2024-01-15                                               │
│                                                                              │
│  Tasks:                                                                     │
│  1. Extract entities (people, systems, projects, organizations)             │
│  2. Identify relationships between entities                                 │
│  3. Map speaker labels to names (infer from context + participants)        │
│  4. Identify up to 10 critical visual moments (diagrams, code, slides)     │
│  5. Extract main topics                                                     │
│                                                                              │
│  WRITE OUTPUT to: /data/temp/analysis_vid-123.txt                          │
│                                                                              │
│  Use this EXACT pipe-delimited format:                                      │
│                                                                              │
│  ENTITY|name|type|description                                               │
│  REL|source|relation|target|timestamp_seconds                               │
│  SPEAKER|label|name|confidence                                              │
│  FRAME|timestamp_seconds|reason                                             │
│  TOPIC|name                                                                 │
│                                                                              │
│  Types: person, system, project, organization, concept                      │
│  Relations: replaced, part_of, works_with, works_on, explained_by          │
│  """                                                                        │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  CLAUDE WRITES OUTPUT FILE (pipe-delimited, easy to parse)                  │
│                                                                              │
│  /data/temp/analysis_vid-123.txt:                                           │
│                                                                              │
│  # Entities                                                                 │
│  ENTITY|AWS Cognito|system|Authentication service for user management      │
│  ENTITY|Auth0|system|Previous authentication provider                       │
│  ENTITY|John Smith|person|Tech lead discussing migration                    │
│  ENTITY|Sarah Chen|person|Team member                                       │
│                                                                              │
│  # Relationships                                                            │
│  REL|AWS Cognito|replaced|Auth0|125                                         │
│  REL|John Smith|works_on|AWS Cognito|45                                     │
│                                                                              │
│  # Speaker Mapping                                                          │
│  SPEAKER|SPEAKER_00|John Smith|0.9                                          │
│  SPEAKER|SPEAKER_01|Sarah Chen|0.85                                         │
│                                                                              │
│  # Critical Frames                                                          │
│  FRAME|15|Screen sharing - architecture diagram visible                     │
│  FRAME|340|Code snippet being discussed                                     │
│  FRAME|892|Deployment pipeline shown                                        │
│                                                                              │
│  # Topics                                                                   │
│  TOPIC|authentication                                                       │
│  TOPIC|migration                                                            │
│  TOPIC|AWS services                                                         │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Step 2: Frame Extraction (FFmpeg)

Extract only the frames Claude identified as critical:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  FRAME EXTRACTION TASK                                                       │
│                                                                              │
│  Input: critical_frames from Claude response                                │
│                                                                              │
│  For each critical frame:                                                   │
│    ffmpeg -ss 15 -i video.mp4 -frames:v 1 -q:v 2 screenshots/00015.jpg     │
│    ffmpeg -ss 340 -i video.mp4 -frames:v 1 -q:v 2 screenshots/00340.jpg    │
│                                                                              │
│  Output: JPG files in data/videos/screenshots/{video_id}/                   │
│                                                                              │
│  Note: Max frames controlled by prompt (default: 10)                        │
│        Only extracts what Claude deemed important                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Step 3: Frame Description (Claude per frame)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  FRAME DESCRIPTION TASK                                                      │
│                                                                              │
│  For each extracted frame, Claude reads the image file directly:            │
│                                                                              │
│  Prompt:                                                                    │
│  """                                                                        │
│  VIEW THIS IMAGE: /data/videos/screenshots/vid-123/00015.jpg               │
│                                                                              │
│  This screenshot was captured at 0:15 during a technical meeting.          │
│  Context from transcript: 'Let me share my screen... As you can see        │
│  in the diagram...'                                                         │
│                                                                              │
│  WRITE OUTPUT to: /data/temp/frame_vid-123_00015.txt                       │
│                                                                              │
│  Use this EXACT pipe-delimited format:                                      │
│  CONTENT_TYPE|type                                                          │
│  TEXT|extracted visible text (one line, use spaces not newlines)           │
│  DESC|visual description                                                    │
│  DETAIL|technical detail (one per line, can have multiple)                  │
│                                                                              │
│  Content types: diagram, code, slide, terminal, whiteboard, screen_share   │
│  """                                                                        │
│                                                                              │
│  Claude reads the image and writes:                                         │
│                                                                              │
│  /data/temp/frame_vid-123_00015.txt:                                        │
│                                                                              │
│  CONTENT_TYPE|architecture_diagram                                          │
│  TEXT|API Gateway → Auth Service → User DB                                  │
│  DESC|Architecture diagram showing three-tier system with REST connections │
│  DETAIL|microservices                                                       │
│  DETAIL|JWT authentication                                                  │
│  DETAIL|PostgreSQL database                                                 │
│  DETAIL|REST API                                                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Frame Description Parser

```python
def parse_frame_description(text: str) -> dict:
    """Parse Claude's frame description output."""
    result = {
        "content_type": None,
        "extracted_text": None,
        "description": None,
        "technical_details": []
    }

    for line in text.strip().split('\n'):
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        parts = line.split('|', 1)  # Split on first | only
        if len(parts) != 2:
            continue

        record_type, value = parts[0], parts[1]

        if record_type == 'CONTENT_TYPE':
            result["content_type"] = value
        elif record_type == 'TEXT':
            result["extracted_text"] = value
        elif record_type == 'DESC':
            result["description"] = value
        elif record_type == 'DETAIL':
            result["technical_details"].append(value)

    return result
```

### A2: Speaker Mapping (Display Only)

Claude infers speaker names for **UI display only** (not indexed for search):

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  SPEAKER MAPPING FLOW (Display Only)                                         │
│                                                                              │
│  1. WhisperX (Phase 1): Labels speakers as SPEAKER_00, SPEAKER_01          │
│                                                                              │
│  2. Claude Analysis (Phase 3): Infers actual names from context            │
│     - "I agree, John" → SPEAKER_00 is probably not John                    │
│     - "Thanks Sarah for sharing" → SPEAKER who shared is Sarah             │
│     - Matches against participants list when provided                       │
│                                                                              │
│  3. Auto-populate speaker_mappings table                                    │
│     INSERT INTO speaker_mappings (video_id, speaker_label, speaker_name,   │
│                                   confidence, source)                       │
│     VALUES ('vid-123', 'SPEAKER_00', 'John Smith', 0.85, 'claude')         │
│                                                                              │
│  4. User can override via UI if Claude got it wrong                        │
│     PUT /api/videos/{id}/speakers                                          │
│     { "SPEAKER_00": "Mike Johnson" }  ← Manual correction                  │
│                                                                              │
│  5. UI resolves names at render time (NOT stored in segments)              │
│     [0:00] John Smith: "We need to discuss..."                             │
│     [0:08] SPEAKER_02: "I have a question..."  ← Unmapped                  │
│                                                                              │
│  NOT INDEXED: Speaker names not in OpenSearch. Use entity search for       │
│  finding people: GET /api/search?entity=john&entity_type=person            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Database Schema (Phase 3 Additions)

### entities

```sql
CREATE TYPE entity_type AS ENUM (
    'person', 'system', 'project', 'organization', 'concept', 'date', 'other'
);

CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    canonical_name VARCHAR(255) NOT NULL,
    type entity_type NOT NULL,
    description TEXT,
    aliases TEXT[],
    first_seen DATE,
    last_seen DATE,
    mention_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(canonical_name, type)
);

CREATE INDEX idx_entities_type ON entities(type);
CREATE INDEX idx_entities_canonical ON entities(canonical_name);
CREATE INDEX idx_entities_aliases ON entities USING GIN(aliases);
```

### entity_mentions

```sql
CREATE TABLE entity_mentions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    segment_id UUID NOT NULL REFERENCES segments(id) ON DELETE CASCADE,
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    timestamp FLOAT NOT NULL,
    context TEXT,  -- Brief quote showing the mention
    confidence FLOAT DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_entity_mentions_entity ON entity_mentions(entity_id);
CREATE INDEX idx_entity_mentions_segment ON entity_mentions(segment_id);
CREATE INDEX idx_entity_mentions_video ON entity_mentions(video_id);
```

### entity_relationships

```sql
CREATE TABLE entity_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    target_entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    relation_type VARCHAR(100) NOT NULL,
    video_id UUID REFERENCES videos(id) ON DELETE SET NULL,
    timestamp FLOAT,
    confidence FLOAT DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(source_entity_id, target_entity_id, relation_type)
);

-- Relation types: migrated_from, replaced_by, part_of, works_with, explained_by
```

### topics

```sql
CREATE TABLE topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    parent_topic_id UUID REFERENCES topics(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE topic_mentions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    segment_id UUID NOT NULL REFERENCES segments(id) ON DELETE CASCADE,
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    timestamp FLOAT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);
```

### screenshots

```sql
CREATE TABLE screenshots (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    timestamp FLOAT NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    thumbnail_path VARCHAR(500),
    reason TEXT,              -- Why Claude flagged this frame as critical
    content_type VARCHAR(50), -- diagram, code, slide, terminal, etc.
    extracted_text TEXT,      -- Text visible in image (extracted by Claude)
    description TEXT,         -- Claude's visual description
    technical_details TEXT[], -- Technical concepts identified
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_screenshots_video ON screenshots(video_id);
CREATE INDEX idx_screenshots_video_time ON screenshots(video_id, timestamp);
CREATE INDEX idx_screenshots_content_type ON screenshots(content_type);
```

### speaker_mappings

```sql
-- Maps WhisperX speaker labels (SPEAKER_00) to actual names (John)
CREATE TABLE speaker_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    speaker_label VARCHAR(50) NOT NULL,   -- SPEAKER_00, SPEAKER_01, etc.
    speaker_name VARCHAR(100) NOT NULL,   -- John, Sarah, etc.
    confidence FLOAT DEFAULT 1.0,         -- Claude's confidence in the mapping
    source VARCHAR(20) DEFAULT 'claude',  -- 'claude' or 'manual'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(video_id, speaker_label)
);

CREATE INDEX idx_speaker_mappings_video ON speaker_mappings(video_id);
```

Note: The `segments.speaker` column is created in Phase 1 and populated by WhisperX during transcription. Claude auto-populates mappings; users can override via UI (source='manual').

---

## OpenSearch Index Updates

### segments_index (modified)

```json
{
  "mappings": {
    "properties": {
      "entities": { "type": "keyword" },
      "entity_types": { "type": "keyword" },
      "topics": { "type": "keyword" }
    }
  }
}
```

Note: `speaker` field (SPEAKER_00) is stored in PostgreSQL for display but NOT indexed in OpenSearch. Speaker names are resolved at render time from `speaker_mappings` table.

### entities_index (new)

```json
{
  "mappings": {
    "properties": {
      "id": { "type": "keyword" },
      "name": {
        "type": "text",
        "fields": {
          "keyword": { "type": "keyword" },
          "fuzzy": {
            "type": "text",
            "analyzer": "fuzzy_analyzer"
          }
        }
      },
      "canonical_name": { "type": "keyword" },
      "type": { "type": "keyword" },
      "description": { "type": "text" },
      "aliases": {
        "type": "text",
        "fields": {
          "keyword": { "type": "keyword" }
        }
      },
      "description_embedding": {
        "type": "knn_vector",
        "dimension": 768
      },
      "mention_count": { "type": "integer" },
      "video_ids": { "type": "keyword" }
    }
  },
  "settings": {
    "analysis": {
      "analyzer": {
        "fuzzy_analyzer": {
          "tokenizer": "standard",
          "filter": ["lowercase", "edge_ngram_filter"]
        }
      },
      "filter": {
        "edge_ngram_filter": {
          "type": "edge_ngram",
          "min_gram": 2,
          "max_gram": 15
        }
      }
    }
  }
}
```

---

## Search Enhancements

### S4: Entity Search

```python
# GET /api/search?q=authentication&entity=cognito&entity_type=system

async def search(
    q: str,
    entity: Optional[str] = None,      # Filter by entity name
    entity_type: Optional[str] = None, # Filter by entity type (person, system, etc.)
    ...
):
    query = build_hybrid_query(q)

    if entity:
        query["bool"]["filter"].append({
            "term": {"entities": entity.lower()}
        })

    if entity_type:
        query["bool"]["filter"].append({
            "term": {"entity_types": entity_type}
        })

# Note: No speaker filter - use entity_type=person instead
# "What did John say?" → GET /api/search?q=...&entity=john&entity_type=person
```

### S6: Fuzzy Matching

```python
# OpenSearch fuzzy query for typo tolerance

def fuzzy_entity_search(query: str):
    return {
        "multi_match": {
            "query": query,
            "fields": ["name^3", "name.fuzzy", "aliases"],
            "fuzziness": "AUTO",
            "prefix_length": 2
        }
    }
```

---

## API Contracts

### GET /api/entities

**Response:**
```json
{
  "entities": [
    {
      "id": "ent-123",
      "name": "AWS Cognito",
      "canonical_name": "cognito",
      "type": "system",
      "mention_count": 15,
      "video_count": 3
    }
  ],
  "total": 45,
  "types": ["person", "system", "project"]
}
```

### GET /api/entities/{id}

**Response:**
```json
{
  "id": "ent-123",
  "name": "AWS Cognito",
  "canonical_name": "cognito",
  "type": "system",
  "description": "Authentication service used for user management",
  "aliases": ["Cognito", "AWS Cognito", "Amazon Cognito"],
  "relationships": [
    {
      "type": "replaced",
      "target": { "id": "ent-456", "name": "Auth0" },
      "video_title": "Auth Migration Meeting",
      "timestamp": 125.5
    }
  ],
  "mentions": [
    {
      "video_id": "vid-789",
      "video_title": "Auth Migration Meeting",
      "timestamp": 45.2,
      "context": "We decided to migrate to Cognito because...",
      "speaker": "John"
    }
  ],
  "mention_count": 15,
  "first_seen": "2024-01-15",
  "last_seen": "2024-03-20"
}
```

### GET /api/videos/{id}/screenshots

**Response:**
```json
{
  "screenshots": [
    {
      "id": "ss-001",
      "timestamp": 125.0,
      "url": "/api/screenshots/ss-001",
      "thumbnail_url": "/api/screenshots/ss-001/thumb",
      "ocr_text": "Authentication Flow Diagram...",
      "description": "Architecture diagram showing OAuth flow",
      "is_key_frame": true
    }
  ]
}
```

---

## Frontend: Entity Detail Page

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  ← Back to Search                                          Entity: System   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  AWS Cognito                                                                │
│  ══════════                                                                 │
│  Authentication service used for user management                            │
│                                                                             │
│  Also known as: Cognito, Amazon Cognito                                     │
│  First mentioned: Jan 15, 2024  |  Last mentioned: Mar 20, 2024            │
│  Total mentions: 15 across 3 videos                                         │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  Relationships                                                              │
│  ─────────────                                                              │
│  • Replaced → Auth0 (mentioned in Auth Migration Meeting @ 2:05)           │
│  • Part of → AWS Services                                                   │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  Mentions Timeline                                                          │
│  ─────────────────                                                          │
│                                                                             │
│  Auth Migration Meeting (Jan 15, 2024)                                      │
│  ├─ @ 0:45  "We decided to migrate to Cognito because..." (John)           │
│  ├─ @ 2:05  "Cognito replaced Auth0 last quarter" (Sarah)                  │
│  └─ @ 5:30  "The Cognito setup was straightforward" (John)                 │
│                                                                             │
│  Tech Review (Feb 20, 2024)                                                 │
│  └─ @ 15:30 "Cognito has been working well for us" (Mike)                  │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Frontend: Visual Content Display (P4)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  Video Player                                                               │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │                                                                       │ │
│  │                        [Video Content]                                │ │
│  │                                                                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│  ▶ ──●────────────────────────────────────────────────────────── 45:00    │
│       │    │         │                   │                                 │
│       📷   📷        📷                  📷  ← Screenshot markers          │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│  Screenshots                                                                │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐                       │
│  │ [thumb] │  │ [thumb] │  │ [thumb] │  │ [thumb] │                       │
│  │  2:05   │  │  8:30   │  │ 15:45   │  │ 32:10   │                       │
│  │ "Auth   │  │ "Code   │  │ "Arch   │  │ "Deploy │                       │
│  │  flow"  │  │  snip"  │  │  diag"  │  │  steps" │                       │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘                       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Status Flow Update

```
Phase 1:
UPLOADED → PROCESSING → TRANSCRIBING → CHUNKING → INDEXING → READY
                            │
                            └── Includes speaker diarization (WhisperX)

Phase 3 (extended):
UPLOADED → PROCESSING → TRANSCRIBING → CHUNKING
                                          │
                                          ▼
                                      ANALYZING
                                (single Claude call:
                                 entities, speakers,
                                 critical frame timestamps)
                                          │
                                          ▼
                                   EXTRACTING_FRAMES
                                    (FFmpeg: only
                                     critical frames)
                                          │
                                          ▼
                                  DESCRIBING_FRAMES
                                   (Claude per frame:
                                    visual description)
                                          │
                                          ▼
                                      INDEXING → READY
```

New statuses: `analyzing`, `extracting_frames`, `describing_frames`

---

## What's Deferred

| Component | Phase |
|-----------|-------|
| Deep Mode (REST API tools) | Phase 4 |
| Neo4j knowledge graph | Phase 5 |
| Topic timelines | Phase 5 |
| Entity relationship visualization | Phase 5 |

---

## Dependencies

Phase 3 provides critical data for Phase 4 (Agentic Search):
- Entity extraction enables `get_entity_info` API
- Entity type=person enables people search (replaces speaker search)
- Topics enable `get_topic_timeline` API
- Screenshots provide visual context for complex queries

---

## Success Criteria

- [ ] Single Claude call extracts entities, relationships, speaker mapping, critical frames
- [ ] Entities searchable - "Everything about [Cognito]" queries work
- [ ] Entity type filter works - `entity_type=person` finds people
- [ ] Fuzzy matching handles typos ("congito" → "Cognito")
- [ ] Speaker names displayed in transcript UI (resolved from mappings)
- [ ] Users can override speaker mappings via UI
- [ ] Only critical frames extracted (max 10 per video, Claude-identified)
- [ ] Frame descriptions include extracted text (no separate OCR library)
- [ ] Screenshots displayed in video timeline
- [ ] Screenshot text content searchable

Note: Speaker labels (SPEAKER_00) from WhisperX. Names are display-only, not indexed for search. Use entity search (type=person) for finding people.
