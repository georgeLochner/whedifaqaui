# Data Model

## Overview

Whedifaqaui uses a dual-database architecture:
- **PostgreSQL**: Source of truth for all structured data
- **OpenSearch**: Search indices optimized for hybrid retrieval

Data flows from PostgreSQL to OpenSearch during the indexing phase.

### Tables by Phase

| Table | Phase | Description |
|-------|-------|-------------|
| `videos` | 1 | Video metadata and processing status |
| `transcripts` | 1 | Full transcript text per video |
| `segments` | 1 | Chunked transcript segments with speaker labels |
| `system_settings` | 1 | Configurable system settings |
| `generated_documents` | 2 | AI-generated summary documents |
| `entities` | 3 | Extracted entities (people, systems, projects) |
| `entity_mentions` | 3 | Links entities to segments |
| `entity_relationships` | 3 | Relationships between entities |
| `topics` | 3 | Extracted topics/concepts |
| `topic_mentions` | 3 | Links topics to segments |
| `speaker_mappings` | 3 | Maps SPEAKER_00 → actual names |
| `screenshots` | 3 | Critical frame captures with descriptions |
| `user_comments` | 6 | User annotations on videos |
| `conversations` | 7 | Saved conversation sessions |
| `conversation_messages` | 7 | Messages within conversations |

## PostgreSQL Schema

### Entity Relationship Diagram

```
┌─────────────────┐       ┌─────────────────────┐       ┌─────────────────┐
│     videos      │       │     transcripts     │       │    segments     │
├─────────────────┤       ├─────────────────────┤       ├─────────────────┤
│ id (PK)         │──────<│ id (PK)             │──────<│ id (PK)         │
│ title           │       │ video_id (FK)       │       │ transcript_id   │
│ file_path       │       │ full_text           │       │ start_time      │
│ processed_path  │       │ language            │       │ end_time        │
│ duration        │       │ created_at          │       │ text            │
│ recording_date  │       └─────────────────────┘       │ speaker         │
│ participants    │                                     │ embedding_id    │
│ context_notes   │                                     └────────┬────────┘
│ status          │                                              │
│ created_at      │                                              │
│ updated_at      │       ┌─────────────────────┐                │
└─────────────────┘       │     entities        │                │
                          ├─────────────────────┤                │
                          │ id (PK)             │                │
                          │ name                │                │
                          │ canonical_name      │                │
                          │ type                │                │
                          │ description         │                │
                          │ first_seen          │                │
                          │ last_seen           │                │
                          │ mention_count       │                │
                          └──────────┬──────────┘                │
                                     │                           │
                                     │                           │
                          ┌──────────┴───────────────────────────┴──────┐
                          │            entity_mentions                   │
                          ├─────────────────────────────────────────────┤
                          │ id (PK)                                     │
                          │ entity_id (FK)                              │
                          │ segment_id (FK)                             │
                          │ video_id (FK)                               │
                          │ timestamp                                   │
                          │ confidence                                  │
                          └─────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                        entity_relationships                              │
├─────────────────────────────────────────────────────────────────────────┤
│ id (PK)                                                                 │
│ source_entity_id (FK) ─────────────────────────────────────► entities   │
│ target_entity_id (FK) ─────────────────────────────────────► entities   │
│ relation_type (e.g., "migrated_from", "explained_by", "part_of")       │
│ video_id (FK) - where this relationship was established                 │
│ timestamp - when in the video                                           │
│ confidence                                                              │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                             topics                                       │
├─────────────────────────────────────────────────────────────────────────┤
│ id (PK)                                                                 │
│ name                                                                    │
│ description                                                             │
│ parent_topic_id (FK, self-referential) ────────────────────► topics     │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                          topic_mentions                                  │
├─────────────────────────────────────────────────────────────────────────┤
│ id (PK)                                                                 │
│ topic_id (FK) ─────────────────────────────────────────────► topics     │
│ segment_id (FK) ───────────────────────────────────────────► segments   │
│ video_id (FK) ─────────────────────────────────────────────► videos     │
│ timestamp                                                               │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                          user_comments                                   │
├─────────────────────────────────────────────────────────────────────────┤
│ id (PK)                                                                 │
│ video_id (FK) ─────────────────────────────────────────────► videos     │
│ timestamp                                                               │
│ comment_text                                                            │
│ created_at                                                              │
└─────────────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────────────┐
│                        generated_documents                               │
├─────────────────────────────────────────────────────────────────────────┤
│ id (PK)                                                                 │
│ session_id                                                              │
│ title                                                                   │
│ content (markdown)                                                      │
│ source_segments[] (array of segment IDs)                                │
│ created_at                                                              │
└─────────────────────────────────────────────────────────────────────────┘
```

### Table Definitions

#### videos (Phase 1)

```sql
CREATE TABLE videos (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title VARCHAR(255) NOT NULL,
    file_path VARCHAR(500) NOT NULL,
    processed_path VARCHAR(500),
    thumbnail_path VARCHAR(500),
    duration INTEGER,  -- seconds
    recording_date DATE NOT NULL,
    participants TEXT[],  -- array of names
    context_notes TEXT,
    status VARCHAR(50) NOT NULL DEFAULT 'uploaded',
    -- status: uploaded, processing, transcribing, analyzing, ready, error
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_videos_status ON videos(status);
CREATE INDEX idx_videos_recording_date ON videos(recording_date);
```

#### transcripts (Phase 1)

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

#### segments (Phase 1)

```sql
CREATE TABLE segments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    transcript_id UUID NOT NULL REFERENCES transcripts(id) ON DELETE CASCADE,
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    start_time FLOAT NOT NULL,  -- seconds
    end_time FLOAT NOT NULL,    -- seconds
    text TEXT NOT NULL,
    summary TEXT,  -- LLM-generated summary (if enabled, Phase 2+)
    speaker VARCHAR(100),  -- WhisperX speaker label: SPEAKER_00, SPEAKER_01, etc.
    chunking_method VARCHAR(20) DEFAULT 'embedding',  -- 'embedding' or 'llm'
    embedding_indexed BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_segments_video_id ON segments(video_id);
CREATE INDEX idx_segments_transcript_id ON segments(transcript_id);
CREATE INDEX idx_segments_time ON segments(video_id, start_time);
CREATE INDEX idx_segments_chunking_method ON segments(chunking_method);
```

#### entities (Phase 3)

```sql
CREATE TYPE entity_type AS ENUM ('person', 'system', 'project', 'organization', 'concept', 'date', 'other');

CREATE TABLE entities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    canonical_name VARCHAR(255) NOT NULL,  -- normalized form
    type entity_type NOT NULL,
    description TEXT,
    aliases TEXT[],  -- alternative names that map to this entity
    first_seen DATE,
    last_seen DATE,
    mention_count INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(canonical_name, type)
);

CREATE INDEX idx_entities_type ON entities(type);
CREATE INDEX idx_entities_canonical ON entities(canonical_name);
```

#### entity_mentions (Phase 3)

```sql
CREATE TABLE entity_mentions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    segment_id UUID NOT NULL REFERENCES segments(id) ON DELETE CASCADE,
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    timestamp FLOAT NOT NULL,  -- seconds into video
    confidence FLOAT DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_entity_mentions_entity ON entity_mentions(entity_id);
CREATE INDEX idx_entity_mentions_segment ON entity_mentions(segment_id);
CREATE INDEX idx_entity_mentions_video ON entity_mentions(video_id);
```

#### entity_relationships (Phase 3)

```sql
CREATE TABLE entity_relationships (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    source_entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    target_entity_id UUID NOT NULL REFERENCES entities(id) ON DELETE CASCADE,
    relation_type VARCHAR(100) NOT NULL,
    -- e.g., "migrated_from", "replaced_by", "explained_by", "part_of", "works_with"
    video_id UUID REFERENCES videos(id) ON DELETE SET NULL,
    timestamp FLOAT,
    confidence FLOAT DEFAULT 1.0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(source_entity_id, target_entity_id, relation_type)
);

CREATE INDEX idx_entity_rel_source ON entity_relationships(source_entity_id);
CREATE INDEX idx_entity_rel_target ON entity_relationships(target_entity_id);
CREATE INDEX idx_entity_rel_type ON entity_relationships(relation_type);
```

#### topics (Phase 3)

```sql
CREATE TABLE topics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL UNIQUE,
    description TEXT,
    parent_topic_id UUID REFERENCES topics(id) ON DELETE SET NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_topics_parent ON topics(parent_topic_id);
```

#### topic_mentions (Phase 3)

```sql
CREATE TABLE topic_mentions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    topic_id UUID NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
    segment_id UUID NOT NULL REFERENCES segments(id) ON DELETE CASCADE,
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    timestamp FLOAT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_topic_mentions_topic ON topic_mentions(topic_id);
CREATE INDEX idx_topic_mentions_video ON topic_mentions(video_id);
```

#### speaker_mappings (Phase 3)

Maps WhisperX speaker labels (SPEAKER_00) to inferred or user-corrected names.

```sql
CREATE TABLE speaker_mappings (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    video_id UUID NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    speaker_label VARCHAR(50) NOT NULL,   -- SPEAKER_00, SPEAKER_01, etc.
    speaker_name VARCHAR(100) NOT NULL,   -- John Smith, Sarah Chen, etc.
    confidence FLOAT DEFAULT 1.0,         -- Claude's confidence in the mapping
    source VARCHAR(20) DEFAULT 'claude',  -- 'claude' or 'manual'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),

    UNIQUE(video_id, speaker_label)
);

CREATE INDEX idx_speaker_mappings_video ON speaker_mappings(video_id);
```

#### screenshots (Phase 3)

Critical frames extracted from videos with Claude-generated descriptions.

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

#### generated_documents (Phase 2)

AI-generated summary documents from chat sessions.

```sql
CREATE TABLE generated_documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    session_id VARCHAR(100),  -- Browser session or user session
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,    -- Markdown content
    source_segment_ids UUID[],  -- Segments used to generate
    source_video_ids UUID[],    -- Videos referenced
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_documents_session ON generated_documents(session_id);
```

#### system_settings (Phase 1)

```sql
CREATE TABLE system_settings (
    key VARCHAR(100) PRIMARY KEY,
    value JSONB NOT NULL,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Default settings inserted on system initialization
INSERT INTO system_settings (key, value) VALUES
    ('chunking', '{
        "mode": "embedding",
        "embedding": {
            "similarity_threshold": 0.5,
            "min_chunk_tokens": 100,
            "max_chunk_tokens": 500
        },
        "llm": {
            "include_summaries": true
        }
    }'),
    ('analysis', '{
        "entity_extraction": {
            "enabled": true,
            "extract_relationships": true
        },
        "summaries": {
            "generate": false,
            "embed": false
        }
    }'),
    ('whisperx', '{
        "model": "large-v2",
        "device": "cuda",
        "compute_type": "float16",
        "language": "en",
        "batch_size": 16
    }'),
    -- Note: Speaker diarization is always enabled (built into WhisperX)
    ('search', '{
        "default_mode": "quick",
        "results_per_query": 10,
        "hybrid_weight": 0.5
    }');
```

---

## OpenSearch Indices

### segments_index (Phase 1, extended Phase 3)

Primary index for hybrid search over transcript segments.

**Phase 1 fields**: id, video_id, video_title, transcript_id, text, embedding, start_time, end_time, speaker, recording_date, created_at

**Phase 3 additions**: entities, entity_types, topics

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
          "engine": "lucene",
          "parameters": {
            "ef_construction": 128,
            "m": 16
          }
        }
      },

      "start_time": { "type": "float" },
      "end_time": { "type": "float" },
      "speaker": { "type": "keyword" },

      "entities": { "type": "keyword" },
      "entity_types": { "type": "keyword" },
      "topics": { "type": "keyword" },

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

### entities_index (Phase 3)

Index for entity search and discovery. Created in Phase 3 when entity extraction is added.

```json
{
  "mappings": {
    "properties": {
      "id": { "type": "keyword" },
      "name": { "type": "text" },
      "canonical_name": { "type": "keyword" },
      "type": { "type": "keyword" },
      "description": { "type": "text" },
      "aliases": { "type": "keyword" },

      "description_embedding": {
        "type": "knn_vector",
        "dimension": 768,
        "method": {
          "name": "hnsw",
          "space_type": "cosinesimil",
          "engine": "lucene"
        }
      },

      "mention_count": { "type": "integer" },
      "first_seen": { "type": "date" },
      "last_seen": { "type": "date" },

      "video_ids": { "type": "keyword" }
    }
  },
  "settings": {
    "index": {
      "knn": true
    }
  }
}
```

---

## Data Synchronization

### PostgreSQL → OpenSearch Flow

```
┌─────────────────┐
│   PostgreSQL    │
│   (segments)    │
└────────┬────────┘
         │
         │ After insert/update
         ▼
┌─────────────────────────────────────────┐
│          Indexing Service               │
│                                         │
│  1. Load segment from PostgreSQL        │
│  2. Generate embedding if not cached    │
│  3. Resolve entity references           │
│  4. Build OpenSearch document           │
│  5. Upsert to segments_index            │
│                                         │
└─────────────────────────────────────────┘
         │
         ▼
┌─────────────────┐
│   OpenSearch    │
│ (segments_index)│
└─────────────────┘
```

### Consistency Model

- PostgreSQL is the **source of truth**
- OpenSearch is a **derived index** for search
- If indices become inconsistent, they can be rebuilt from PostgreSQL
- Indexing happens asynchronously via Celery tasks

---

## Phase 5: Neo4j Integration

When Neo4j is added in Phase 5, entity relationships will be synced:

```
PostgreSQL (entities, entity_relationships)
         │
         │ Sync on change
         ▼
┌─────────────────────────────────────────┐
│                 Neo4j                    │
│                                         │
│  (Person:John)-[:EXPLAINED]->(System:Cognito)
│  (System:Cognito)-[:MIGRATED_FROM]->(System:Auth0)
│  (Person:Sarah)-[:WORKS_WITH]->(Person:John)
│                                         │
└─────────────────────────────────────────┘
```

The Neo4j schema will mirror the entity_relationships table but optimized for graph traversal.
