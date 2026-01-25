# Processing Pipeline

## Overview

When a video is uploaded, it goes through a multi-stage processing pipeline. Each stage is implemented as a Celery task, allowing for asynchronous processing and fault tolerance.

## Pipeline Stages

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         VIDEO UPLOAD                                         │
│                                                                              │
│  User uploads MKV file with metadata (title, date, participants, notes)     │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 1: UPLOAD PROCESSING                                    Status: UPLOADED
│                                                                              │
│  1. Save original MKV to /data/videos/original/{video_id}.mkv               │
│  2. Create video record in PostgreSQL                                       │
│  3. Queue video_processing task                                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 2: VIDEO PROCESSING (Celery Task)                    Status: PROCESSING
│                                                                              │
│  1. Extract metadata with FFprobe (duration, codecs, resolution)            │
│  2. Attempt remux to MP4 (fast, no re-encode)                               │
│     - If codecs incompatible, transcode to H.264/AAC                        │
│  3. Save to /data/videos/processed/{video_id}.mp4                           │
│  4. Generate thumbnail at 10% mark                                          │
│  5. Extract audio to WAV (16kHz mono for Whisper)                           │
│  6. Save to /data/videos/audio/{video_id}.wav                               │
│  7. Queue transcription task                                                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 3: TRANSCRIPTION (Celery Task)                     Status: TRANSCRIBING
│                                                                              │
│  1. Load Whisper model (large-v2 or medium)                                 │
│  2. Transcribe audio file with word-level timestamps                        │
│  3. Collect Whisper segments (natural speech boundaries)                    │
│  4. Perform speaker diarization (optional, via WhisperX)                    │
│  5. Create transcript record in PostgreSQL                                  │
│  6. Save raw Whisper segments to /data/transcripts/{video_id}.json          │
│  7. Queue semantic chunking task                                            │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 4: SEMANTIC CHUNKING (Celery Task)                   Status: CHUNKING │
│                                                                              │
│  Configurable chunking strategy (see Settings):                             │
│                                                                              │
│  MODE: EMBEDDING-BASED (default, fast, free)                                │
│    1. Load Whisper segments from transcript                                 │
│    2. Generate embeddings for each segment (BGE model)                      │
│    3. Detect semantic boundaries (similarity drops below threshold)         │
│    4. Group segments into chunks (target: 200-500 tokens)                   │
│    5. Generate chunk embeddings                                             │
│                                                                              │
│  MODE: LLM-BASED (better quality, uses Claude Code CLI)                     │
│    1. Build timestamped transcript                                          │
│    2. Ask LLM to identify topic boundaries and chunk summaries              │
│    3. Create chunks based on LLM-defined boundaries                         │
│    4. Generate chunk embeddings (BGE model)                                 │
│                                                                              │
│  MODE: BOTH (for comparison)                                                │
│    - Run both strategies, store with chunking_method label                  │
│    - Enables A/B testing of retrieval quality                               │
│                                                                              │
│  6. Create chunk records in PostgreSQL (with chunking_method)               │
│  7. Queue content analysis task                                             │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 5: CONTENT ANALYSIS (Celery Task)                    Status: ANALYZING
│                                                                              │
│  Single LLM call with full transcript (via Claude Code CLI):                │
│    1. Feed timestamped transcript to Claude                                 │
│    2. Extract entities with their mention timestamps                        │
│    3. Extract relationships between entities                                │
│    4. Extract topics/concepts                                               │
│                                                                              │
│  Post-processing:                                                           │
│    5. Normalize entity names (canonical form)                               │
│    6. Link mentions to segments by timestamp                                │
│    7. Update mention counts                                                 │
│    8. Queue indexing task                                                   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STAGE 6: INDEXING (Celery Task)                              Status: READY  │
│                                                                              │
│  1. Build OpenSearch documents for each chunk                               │
│  2. Bulk index chunks to segments_index                                     │
│  3. Update entities_index with new/updated entities                         │
│  4. Update video status to READY                                            │
│  5. Clean up temporary audio file                                           │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Semantic Chunking Strategy

### Why Semantic Chunking?

| Strategy | Quality | Speed | Best For |
|----------|---------|-------|----------|
| Fixed size/time | Low | Fast | Prototyping only |
| Whisper segments (as-is) | Medium | Fast | Too granular for embedding |
| **Semantic (embedding-based)** | High | Medium | Production - best tradeoff |
| LLM-guided chunking | Highest | Slow | Too expensive at scale |

Research shows semantic chunking achieves **up to 70% improvement** in retrieval accuracy compared to fixed-size approaches.

### How Semantic Chunking Works

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 1: Whisper Segments (Base Units)                                       │
│                                                                              │
│  Whisper provides natural segments based on audio pauses (1-30 seconds).    │
│  These represent natural speech boundaries - the foundation for chunking.   │
│                                                                              │
│  [Seg1: 0-8s] [Seg2: 8-15s] [Seg3: 15-25s] [Seg4: 25-35s] [Seg5: 35-42s]   │
│  "We need to   "The current  "So we decided "This caused   "But after     │
│   discuss the   system uses    to migrate     some issues    fixing the    │
│   auth system"  Auth0..."      to Cognito"    initially"     config..."    │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 2: Generate Embeddings for Each Segment                                │
│                                                                              │
│  Use BGE model (768 dimensions) to embed each Whisper segment.              │
│  Performance: ~1000 segments/second on GPU                                  │
│                                                                              │
│  [Seg1: vec_1] [Seg2: vec_2] [Seg3: vec_3] [Seg4: vec_4] [Seg5: vec_5]     │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 3: Semantic Boundary Detection                                         │
│                                                                              │
│  Calculate cosine similarity between adjacent segment embeddings.           │
│  When similarity drops below threshold → semantic boundary detected.        │
│                                                                              │
│  sim(1,2)=0.82   sim(2,3)=0.85   sim(3,4)=0.78   sim(4,5)=0.41            │
│       ↑               ↑               ↑               ↑                     │
│    Related        Related         Related      TOPIC CHANGE!               │
│                                                                              │
│  Threshold: 0.5 (configurable)                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 4: Create Semantic Chunks                                              │
│                                                                              │
│  Group segments between semantic boundaries.                                │
│  Enforce min/max token constraints (200-500 tokens).                        │
│                                                                              │
│  ┌─────────────────────────────────┐  ┌─────────────────────────────────┐  │
│  │ Chunk 1 (Seg1 + Seg2 + Seg3 + 4)│  │ Chunk 2 (Seg5 + ...)            │  │
│  │ "We need to discuss the auth    │  │ "But after fixing the config    │  │
│  │  system. The current system     │  │  we were able to deploy..."     │  │
│  │  uses Auth0. So we decided to   │  │                                 │  │
│  │  migrate to Cognito. This       │  │ Topic: Deployment               │  │
│  │  caused some issues initially"  │  │                                 │  │
│  │                                 │  │                                 │  │
│  │ Topic: Auth Migration           │  │                                 │  │
│  └─────────────────────────────────┘  └─────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 5: Generate Chunk Embeddings                                           │
│                                                                              │
│  Re-embed the combined chunk text for better retrieval quality.             │
│  This captures the full semantic meaning of the coherent chunk.             │
│                                                                              │
│  Chunk 1 embedding: [0.12, -0.45, 0.78, ...]  (768 dimensions)             │
│  Chunk 2 embedding: [0.34, -0.21, 0.56, ...]  (768 dimensions)             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│  STEP 6 (Optional): LLM Summary Generation                                   │
│                                                                              │
│  Generate a brief summary for each chunk via Claude Code CLI.               │
│  Summaries enable concept-level search (embedding the summary too).         │
│                                                                              │
│  Chunk 1 Summary: "Discussion of migrating authentication from Auth0 to    │
│                    AWS Cognito, including initial challenges encountered"   │
│                                                                              │
│  Note: Uses Claude Code CLI - no additional API costs                      │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Chunking Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| `similarity_threshold` | 0.5 | Cosine similarity below this triggers boundary |
| `min_chunk_tokens` | 100 | Minimum tokens per chunk (merge if smaller) |
| `max_chunk_tokens` | 500 | Maximum tokens per chunk (force split if larger) |
| `generate_summaries` | false | Whether to generate LLM summaries |

---

## Stage Details

### Stage 2: Video Processing

```python
# tasks/video_processing.py

import ffmpeg
from celery import shared_task

@shared_task(bind=True, max_retries=3)
def process_video(self, video_id: str):
    video = get_video(video_id)
    update_status(video_id, 'processing')

    try:
        input_path = video.file_path
        output_path = f"/data/videos/processed/{video_id}.mp4"
        audio_path = f"/data/videos/audio/{video_id}.wav"
        thumb_path = f"/data/videos/thumbnails/{video_id}.jpg"

        # 1. Get video metadata
        probe = ffmpeg.probe(input_path)
        duration = float(probe['format']['duration'])

        # 2. Remux or transcode to MP4
        try:
            # Try remux first (fast)
            ffmpeg.input(input_path).output(
                output_path,
                c='copy',  # Copy streams without re-encoding
                movflags='faststart'
            ).overwrite_output().run(capture_stderr=True)
        except ffmpeg.Error:
            # Fallback to transcode
            ffmpeg.input(input_path).output(
                output_path,
                vcodec='libx264',
                acodec='aac',
                preset='medium',
                crf=23,
                movflags='faststart'
            ).overwrite_output().run()

        # 3. Generate thumbnail
        ffmpeg.input(input_path, ss=duration * 0.1).output(
            thumb_path,
            vframes=1,
            vf='scale=320:-1'
        ).overwrite_output().run()

        # 4. Extract audio for transcription
        ffmpeg.input(input_path).output(
            audio_path,
            acodec='pcm_s16le',
            ac=1,  # Mono
            ar=16000  # 16kHz for Whisper
        ).overwrite_output().run()

        # 5. Update database
        update_video(video_id, {
            'processed_path': output_path,
            'thumbnail_path': thumb_path,
            'duration': int(duration)
        })

        # 6. Queue next stage
        transcribe_video.delay(video_id, audio_path)

    except Exception as e:
        update_status(video_id, 'error', str(e))
        raise self.retry(exc=e)
```

### Stage 3: Transcription

```python
# tasks/transcription.py

from faster_whisper import WhisperModel
from celery import shared_task
import json

# Load model once at worker startup
whisper_model = None

def get_whisper_model():
    global whisper_model
    if whisper_model is None:
        whisper_model = WhisperModel(
            "large-v2",
            device="cuda",  # or "cpu"
            compute_type="float16"  # or "int8" for CPU
        )
    return whisper_model

@shared_task(bind=True, max_retries=2)
def transcribe_video(self, video_id: str, audio_path: str):
    update_status(video_id, 'transcribing')

    try:
        model = get_whisper_model()

        # 1. Transcribe with word-level timestamps
        segments_iter, info = model.transcribe(
            audio_path,
            beam_size=5,
            word_timestamps=True,
            language="en"
        )

        # 2. Collect Whisper segments (these are our base units)
        whisper_segments = []
        full_text_parts = []

        for segment in segments_iter:
            whisper_segments.append({
                'id': len(whisper_segments),
                'start': segment.start,
                'end': segment.end,
                'text': segment.text.strip(),
                'words': [
                    {'word': w.word, 'start': w.start, 'end': w.end}
                    for w in segment.words
                ] if segment.words else []
            })
            full_text_parts.append(segment.text.strip())

        full_text = ' '.join(full_text_parts)

        # 3. Create transcript record
        transcript = create_transcript(
            video_id=video_id,
            full_text=full_text,
            language=info.language,
            word_count=len(full_text.split())
        )

        # 4. Save raw Whisper segments as JSON
        transcript_path = f"/data/transcripts/{video_id}.json"
        with open(transcript_path, 'w') as f:
            json.dump({
                'video_id': video_id,
                'transcript_id': str(transcript.id),
                'language': info.language,
                'duration': info.duration,
                'whisper_segments': whisper_segments
            }, f, indent=2)

        # 5. Queue semantic chunking
        semantic_chunk.delay(video_id, str(transcript.id), transcript_path)

    except Exception as e:
        update_status(video_id, 'error', str(e))
        raise self.retry(exc=e)
```

### Stage 4: Semantic Chunking

Stage 4 supports three configurable chunking modes via System Settings.

```python
# tasks/chunking.py

from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
from celery import shared_task
import numpy as np
import json
from app.services.claude import claude

# Load embedding model once
embedding_model = None

def get_embedding_model():
    global embedding_model
    if embedding_model is None:
        embedding_model = SentenceTransformer('BAAI/bge-base-en-v1.5')
    return embedding_model


@shared_task(bind=True)
def semantic_chunk(self, video_id: str, transcript_id: str, transcript_path: str):
    """
    Main chunking task - delegates to configured strategy.
    """
    update_status(video_id, 'chunking')
    config = get_chunking_config()  # From system_settings table

    try:
        with open(transcript_path, 'r') as f:
            data = json.load(f)
        whisper_segments = data['whisper_segments']

        if not whisper_segments:
            raise ValueError("No Whisper segments found")

        # Run configured chunking mode(s)
        if config['mode'] == 'embedding':
            chunks = chunk_embedding_based(whisper_segments, config['embedding'])
            save_chunks(chunks, video_id, transcript_id, method='embedding')

        elif config['mode'] == 'llm':
            chunks = chunk_llm_based(whisper_segments, config['llm'])
            save_chunks(chunks, video_id, transcript_id, method='llm')

        elif config['mode'] == 'both':
            # Run both for comparison
            emb_chunks = chunk_embedding_based(whisper_segments, config['embedding'])
            save_chunks(emb_chunks, video_id, transcript_id, method='embedding')

            llm_chunks = chunk_llm_based(whisper_segments, config['llm'])
            save_chunks(llm_chunks, video_id, transcript_id, method='llm')

        # Queue content analysis
        analyze_content.delay(video_id, transcript_id)

    except Exception as e:
        update_status(video_id, 'error', str(e))
        raise


# =============================================================================
# EMBEDDING-BASED CHUNKING (fast, free, good quality)
# =============================================================================

def chunk_embedding_based(whisper_segments: list, config: dict) -> list:
    """
    Chunk using embedding similarity to detect topic boundaries.
    """
    model = get_embedding_model()

    # Generate embeddings for each Whisper segment
    texts = [seg['text'] for seg in whisper_segments]
    segment_embeddings = model.encode(texts, show_progress_bar=True)

    # Find semantic boundaries
    boundaries = find_semantic_boundaries(
        segment_embeddings,
        config['similarity_threshold']
    )

    # Create chunks from boundaries
    chunks = create_chunks_from_boundaries(
        whisper_segments,
        boundaries,
        config['min_chunk_tokens'],
        config['max_chunk_tokens']
    )

    # Generate chunk embeddings
    chunk_texts = [chunk['text'] for chunk in chunks]
    chunk_embeddings = model.encode(chunk_texts)

    for i, chunk in enumerate(chunks):
        chunk['embedding'] = chunk_embeddings[i].tolist()

    return chunks


# =============================================================================
# LLM-BASED CHUNKING (better quality, ~$0.002/video)
# =============================================================================

def chunk_llm_based(whisper_segments: list, config: dict) -> list:
    """
    Chunk using LLM to identify topic boundaries with full context understanding.
    Uses Claude wrapper module (services/claude.py) for LLM access.
    """
    # Build timestamped transcript
    timestamped_text = build_timestamped_text(whisper_segments)

    # Ask LLM to identify chunks via wrapper module
    prompt = f"""Analyze this timestamped transcript and divide it into semantic chunks.
Each chunk should cover a coherent topic or discussion thread.

Return JSON array:
[
  {{
    "start_time": <seconds>,
    "end_time": <seconds>,
    "summary": "Brief description of what this chunk covers"
  }}
]

Guidelines:
- Create chunks of roughly 1-3 minutes each
- Break at natural topic transitions
- Each chunk should be self-contained enough to be useful in search results
- Timestamps are in [MM:SS] format, convert to total seconds in output

Transcript:
{timestamped_text}

Return only valid JSON array, no other text."""

    # Use Claude wrapper module - no conversation persistence needed for processing
    llm_chunks, _ = claude.query_json(prompt, timeout=300)

    # Build full chunks with text from Whisper segments
    chunks = []
    for llm_chunk in llm_chunks:
        # Find Whisper segments that fall within this chunk's time range
        chunk_segments = [
            seg for seg in whisper_segments
            if seg['start'] >= llm_chunk['start_time']
            and seg['end'] <= llm_chunk['end_time']
        ]

        if not chunk_segments:
            continue

        chunk_text = ' '.join([s['text'] for s in chunk_segments])

        chunks.append({
            'text': chunk_text,
            'start_time': llm_chunk['start_time'],
            'end_time': llm_chunk['end_time'],
            'summary': llm_chunk.get('summary'),
            'whisper_segment_ids': [s['id'] for s in chunk_segments],
            'token_count': len(chunk_text.split())
        })

    # Generate embeddings for search (still using BGE)
    model = get_embedding_model()
    chunk_texts = [chunk['text'] for chunk in chunks]
    chunk_embeddings = model.encode(chunk_texts)

    for i, chunk in enumerate(chunks):
        chunk['embedding'] = chunk_embeddings[i].tolist()

    return chunks


def build_timestamped_text(whisper_segments: list) -> str:
    """Build timestamped transcript string for LLM."""
    lines = []
    for seg in whisper_segments:
        minutes = int(seg['start'] // 60)
        seconds = int(seg['start'] % 60)
        lines.append(f"[{minutes}:{seconds:02d}] {seg['text']}")
    return "\n".join(lines)


# =============================================================================
# SHARED UTILITIES
# =============================================================================

def save_chunks(chunks: list, video_id: str, transcript_id: str, method: str):
    """Save chunks to database with method label."""
    for chunk in chunks:
        create_segment(
            transcript_id=transcript_id,
            video_id=video_id,
            start_time=chunk['start_time'],
            end_time=chunk['end_time'],
            text=chunk['text'],
            summary=chunk.get('summary'),
            embedding=chunk['embedding'],
            whisper_segment_ids=chunk.get('whisper_segment_ids', []),
            token_count=chunk['token_count'],
            chunking_method=method  # 'embedding' or 'llm'
        )


def find_semantic_boundaries(
    embeddings: np.ndarray,
    threshold: float
) -> list:
    """
    Find indices where semantic similarity drops below threshold.
    These are the natural topic boundaries.
    """
    boundaries = [0]  # Start boundary

    for i in range(1, len(embeddings)):
        sim = cosine_similarity(
            [embeddings[i - 1]],
            [embeddings[i]]
        )[0][0]

        if sim < threshold:
            boundaries.append(i)

    boundaries.append(len(embeddings))  # End boundary
    return boundaries


def create_chunks_from_boundaries(
    whisper_segments: list,
    boundaries: list,
    min_tokens: int,
    max_tokens: int
) -> list:
    """
    Create chunks from Whisper segments based on semantic boundaries.
    Enforces min/max token constraints.
    """
    chunks = []

    for i in range(len(boundaries) - 1):
        start_idx = boundaries[i]
        end_idx = boundaries[i + 1]

        # Collect segments in this boundary range
        chunk_segments = whisper_segments[start_idx:end_idx]

        if not chunk_segments:
            continue

        chunk_text = ' '.join([s['text'] for s in chunk_segments])
        token_count = len(chunk_text.split())

        # Handle chunks that are too small
        if token_count < min_tokens and chunks:
            # Merge with previous chunk
            prev_chunk = chunks[-1]
            prev_chunk['text'] += ' ' + chunk_text
            prev_chunk['end_time'] = chunk_segments[-1]['end']
            prev_chunk['whisper_segment_ids'].extend(
                [s['id'] for s in chunk_segments]
            )
            prev_chunk['token_count'] = len(prev_chunk['text'].split())
            continue

        # Handle chunks that are too large
        if token_count > max_tokens:
            # Split into multiple chunks
            sub_chunks = split_large_chunk(chunk_segments, max_tokens)
            chunks.extend(sub_chunks)
            continue

        # Normal chunk
        chunks.append({
            'text': chunk_text,
            'start_time': chunk_segments[0]['start'],
            'end_time': chunk_segments[-1]['end'],
            'whisper_segment_ids': [s['id'] for s in chunk_segments],
            'token_count': token_count
        })

    return chunks


def split_large_chunk(segments: list, max_tokens: int) -> list:
    """Split a large chunk into smaller ones at sentence boundaries."""
    sub_chunks = []
    current_segments = []
    current_tokens = 0

    for seg in segments:
        seg_tokens = len(seg['text'].split())

        if current_tokens + seg_tokens > max_tokens and current_segments:
            # Emit current chunk
            sub_chunks.append({
                'text': ' '.join([s['text'] for s in current_segments]),
                'start_time': current_segments[0]['start'],
                'end_time': current_segments[-1]['end'],
                'whisper_segment_ids': [s['id'] for s in current_segments],
                'token_count': current_tokens
            })
            current_segments = []
            current_tokens = 0

        current_segments.append(seg)
        current_tokens += seg_tokens

    # Don't forget the last chunk
    if current_segments:
        sub_chunks.append({
            'text': ' '.join([s['text'] for s in current_segments]),
            'start_time': current_segments[0]['start'],
            'end_time': current_segments[-1]['end'],
            'whisper_segment_ids': [s['id'] for s in current_segments],
            'token_count': current_tokens
        })

    return sub_chunks


def generate_chunk_summaries(chunks: list) -> None:
    """
    Generate LLM summaries for each chunk.
    Uses Claude wrapper module (services/claude.py) for LLM access.
    """
    for chunk in chunks:
        try:
            prompt = f"""Summarize this transcript segment in one concise sentence:

{chunk['text'][:2000]}

Summary:"""

            # Use Claude wrapper module
            response = claude.query(prompt, timeout=60)
            chunk['summary'] = response.result.strip()

            # Optionally: embed the summary for concept-level search
            # summary_embedding = model.encode([chunk['summary']])[0]
            # update_chunk_summary(chunk['id'], chunk['summary'], summary_embedding)

        except Exception as e:
            chunk['summary'] = None  # Skip on error
```

### Stage 5: Content Analysis

The content analysis stage uses a single LLM call with the full timestamped transcript.
This approach provides better context for entity disambiguation and relationship detection
compared to per-chunk processing.

```python
# tasks/analysis.py

from celery import shared_task
import json
from app.services.claude import claude

@shared_task(bind=True)
def analyze_content(self, video_id: str, transcript_id: str):
    update_status(video_id, 'analyzing')

    try:
        transcript = get_transcript(transcript_id)

        # 1. Build timestamped transcript for LLM
        timestamped_text = build_timestamped_transcript(transcript_id)

        # 2. Single LLM call for entity extraction
        extraction_result = extract_entities_and_relationships(timestamped_text)

        # 3. Save entities to database
        for entity_data in extraction_result['entities']:
            # Normalize to canonical form
            canonical_name = normalize_entity_name(entity_data['name'])

            entity = get_or_create_entity(
                name=entity_data['name'],
                canonical_name=canonical_name,
                entity_type=entity_data['type']
            )

            # Create mention records with timestamps from LLM
            for mention in entity_data['mentions']:
                # Find the segment that contains this timestamp
                segment = find_segment_by_timestamp(transcript_id, mention['timestamp'])

                create_entity_mention(
                    entity_id=entity.id,
                    segment_id=segment.id if segment else None,
                    video_id=video_id,
                    timestamp=mention['timestamp'],
                    context=mention.get('context')
                )

        # 4. Save relationships
        for rel in extraction_result.get('relationships', []):
            source = get_entity_by_name(rel['source'])
            target = get_entity_by_name(rel['target'])
            if source and target:
                create_entity_relationship(
                    source_entity_id=source.id,
                    target_entity_id=target.id,
                    relation_type=rel['relation'],
                    video_id=video_id,
                    timestamp=rel.get('timestamp')
                )

        # 5. Queue indexing
        index_video.delay(video_id, transcript_id)

    except Exception as e:
        update_status(video_id, 'error', str(e))
        raise


def build_timestamped_transcript(transcript_id: str) -> str:
    """Build a timestamped transcript string for LLM consumption."""
    segments = get_segments_ordered(transcript_id)

    lines = []
    for seg in segments:
        # Format: [MM:SS] text
        minutes = int(seg.start_time // 60)
        seconds = int(seg.start_time % 60)
        lines.append(f"[{minutes}:{seconds:02d}] {seg.text}")

    return "\n".join(lines)


def extract_entities_and_relationships(timestamped_transcript: str) -> dict:
    """
    Extract entities and relationships using Claude wrapper module.
    Single call with full transcript for better context and disambiguation.

    Note: For processing tasks like this, we don't persist the conversation.
    A new UUID is generated and discarded after the call.
    """
    prompt = f"""Analyze this timestamped transcript and extract:

1. ENTITIES: Named things (people, systems, projects, organizations, concepts)
2. RELATIONSHIPS: How entities relate to each other

Return JSON with this structure:
{{
  "entities": [
    {{
      "name": "entity name",
      "type": "person|system|project|organization|concept",
      "mentions": [
        {{"timestamp": <seconds>, "context": "brief quote showing usage"}}
      ]
    }}
  ],
  "relationships": [
    {{
      "source": "entity name",
      "relation": "migrated_from|replaced_by|part_of|works_with|explained_by",
      "target": "entity name",
      "timestamp": <seconds where relationship is mentioned>
    }}
  ]
}}

Notes:
- Consolidate entity variations (e.g., "AWS Cognito" and "Cognito" = same entity)
- Timestamps are in [MM:SS] format, convert to total seconds
- Include ALL mentions of each entity

Transcript:
{timestamped_transcript}

Return only valid JSON, no other text."""

    # Use Claude wrapper module - no conversation persistence needed
    result, _ = claude.query_json(prompt, timeout=300)
    return result


def normalize_entity_name(name: str) -> str:
    """Convert entity name to canonical form for deduplication."""
    # Lowercase, strip whitespace, remove common prefixes
    canonical = name.lower().strip()

    # Remove common prefixes
    prefixes = ['aws ', 'amazon ', 'google ', 'microsoft ']
    for prefix in prefixes:
        if canonical.startswith(prefix):
            canonical = canonical[len(prefix):]

    return canonical
```

### Why Full-Transcript Extraction?

| Approach | Pros | Cons |
|----------|------|------|
| **Per-chunk** | Parallelizable, failure isolation | Loses context, poor disambiguation |
| **Full-transcript** | Better disambiguation, relationships visible, timestamps included | Single point of failure |

For typical meeting recordings (1-3 hours, ~20K tokens), the full transcript fits easily
within Claude's context window. The improved extraction quality outweighs the
parallelization benefits of per-chunk processing.

### Handling Long Transcripts

For exceptionally long videos (4+ hours), fall back to chunked processing:

```python
MAX_TRANSCRIPT_TOKENS = 50000  # Conservative limit

def analyze_content(self, video_id: str, transcript_id: str):
    timestamped_text = build_timestamped_transcript(transcript_id)
    token_count = estimate_tokens(timestamped_text)

    if token_count > MAX_TRANSCRIPT_TOKENS:
        # Fall back to chunked processing for very long videos
        return analyze_content_chunked(video_id, transcript_id)

    # Normal full-transcript processing
    extraction_result = extract_entities_and_relationships(timestamped_text)
    ...
```

### Stage 6: Indexing

```python
# tasks/indexing.py

from opensearchpy import OpenSearch
from opensearchpy.helpers import bulk
from celery import shared_task

client = OpenSearch(
    hosts=[{'host': 'localhost', 'port': 9200}],
    http_auth=('admin', 'admin'),
    use_ssl=False
)

@shared_task
def index_video(video_id: str, transcript_id: str):
    video = get_video(video_id)
    chunks = get_chunks_with_embeddings(transcript_id)

    # Build OpenSearch documents
    actions = []
    for chunk in chunks:
        doc = {
            'id': str(chunk.id),
            'video_id': str(video_id),
            'video_title': video.title,
            'transcript_id': str(transcript_id),
            'text': chunk.text,
            'embedding': chunk.embedding,
            'summary': chunk.summary,  # May be None
            'start_time': chunk.start_time,
            'end_time': chunk.end_time,
            'speaker': chunk.speaker,
            'token_count': chunk.token_count,
            'entities': get_chunk_entities(chunk.id),
            'entity_types': get_chunk_entity_types(chunk.id),
            'topics': get_chunk_topics(chunk.id),
            'recording_date': video.recording_date.isoformat(),
            'created_at': chunk.created_at.isoformat()
        }
        actions.append({
            '_index': 'segments_index',
            '_id': str(chunk.id),
            '_source': doc
        })

    # Bulk index
    bulk(client, actions)

    # Update status
    update_status(video_id, 'ready')

    # Clean up temporary audio file
    cleanup_audio(video_id)
```

---

## Error Handling & Retries

| Stage | Max Retries | Retry Delay | On Failure |
|-------|-------------|-------------|------------|
| Video Processing | 3 | 60 seconds | Status → error |
| Transcription | 2 | 120 seconds | Status → error |
| Semantic Chunking | 2 | 60 seconds | Status → error |
| Content Analysis | 1 | 60 seconds | Status → error |
| Indexing | 3 | 30 seconds | Status → error |

---

## Monitoring

Celery tasks emit events that can be monitored via:
- **Flower**: Web-based Celery monitoring
- **Logging**: Structured logs for each task
- **Database**: Video status column tracks progress

---

## Processing Time Estimates

| Stage | Duration (2hr video, GPU) | Duration (2hr video, CPU) |
|-------|---------------------------|---------------------------|
| Video Processing | 2-5 minutes | 5-15 minutes |
| Transcription | 10-20 minutes | 2-4 hours |
| Semantic Chunking | ~30 seconds | ~2 minutes |
| Content Analysis | 3-5 minutes | 3-5 minutes |
| Indexing | 1-2 minutes | 1-2 minutes |
| **Total** | **~20-35 minutes** | **~2.5-4.5 hours** |

Note: Semantic chunking is fast because embedding generation on GPU processes ~1000 segments/second.

---

## What Gets Indexed

| Content | Embedding | Purpose |
|---------|-----------|---------|
| **Chunk text** | Yes | Primary retrieval |
| **Chunk summary** | Optional | Concept-level search |
| **Entity descriptions** | Phase 3 | Entity-focused search |

---

## Configuration Options

All settings are configurable via the System Settings UI.

```python
# config.py

CHUNKING_CONFIG = {
    # Chunking strategy: 'embedding' | 'llm' | 'both'
    'mode': 'embedding',

    # Embedding-based chunking settings
    'embedding': {
        'similarity_threshold': 0.5,  # Lower = more boundaries
        'min_chunk_tokens': 100,
        'max_chunk_tokens': 500,
    },

    # LLM-based chunking settings
    'llm': {
        'include_summaries': True,  # LLM provides chunk summaries
        # Model determined by Claude Code CLI configuration
    },
}

ANALYSIS_CONFIG = {
    # Entity extraction (uses Claude Code CLI)
    'entity_extraction': {
        'enabled': True,
        'extract_relationships': True,
        # Model determined by Claude Code CLI configuration
    },

    # Chunk summaries (separate from LLM chunking)
    'summaries': {
        'generate': False,  # Enable for better concept search
        'embed': False,     # Embed summaries for retrieval
    },
}

WHISPER_CONFIG = {
    'model': 'large-v2',  # or 'medium' for faster processing
    'device': 'cuda',     # or 'cpu'
    'compute_type': 'float16',  # or 'int8' for CPU
    'language': 'en',
    'speaker_diarization': True,  # Phase 3
}

EMBEDDING_CONFIG = {
    'model': 'BAAI/bge-base-en-v1.5',
    'dimensions': 768,
}

SEARCH_CONFIG = {
    'default_mode': 'quick',  # 'quick' | 'deep'
    'results_per_query': 10,
    'hybrid_weight': 0.5,  # 0 = pure BM25, 1 = pure vector
}
```

### Configuration via Settings UI

These settings are stored in a `system_settings` table and exposed via the Settings page:

| Setting | UI Control | Default |
|---------|------------|---------|
| Chunking mode | Radio buttons | `embedding` |
| Similarity threshold | Slider (0.3-0.8) | 0.5 |
| Entity extraction | Toggle | On |
| Speaker diarization | Toggle | On |
| Query mode | Dropdown | Quick |
| Hybrid search weight | Slider | 0.5 |

Changes apply to newly processed videos. Existing videos can be reprocessed via the Library view.
