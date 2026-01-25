# Phase 1 Test Specification

**Phase**: MVP Core
**Goal**: Upload → Transcribe → Basic Search → Play at Timestamp
**Stories Covered**: V1, V2, V3, P1, P2, P3, S1, S3, M1

---

## Table of Contents

1. [Test Strategy Overview](#1-test-strategy-overview)
2. [Test Resources](#2-test-resources)
3. [Story-by-Story Test Specifications](#3-story-by-story-test-specifications)
4. [End-to-End Test Scenarios](#4-end-to-end-test-scenarios)
5. [Playwright Screenshot Verification](#5-playwright-screenshot-verification)
6. [Test Data Management](#6-test-data-management)
7. [Success Criteria](#7-success-criteria)

---

## 1. Test Strategy Overview

### Test Pyramid

```
                    ┌─────────────────┐
                    │   E2E Tests     │  ← Playwright (3-5 critical flows)
                    │   (Slow, Few)   │
                   ─┼─────────────────┼─
                  / │ Integration     │ \  ← API + DB + Services (10-15 tests)
                 /  │ Tests           │  \
               ─────┼─────────────────┼─────
              /     │ Unit Tests      │     \  ← Pure logic tests (50+ tests)
             /      │ (Fast, Many)    │      \
            ────────┴─────────────────┴────────
```

### Testing Frameworks

| Layer | Backend | Frontend |
|-------|---------|----------|
| Unit | pytest | vitest |
| Integration | pytest + TestClient | vitest + MSW |
| E2E | pytest (API only) | Playwright |
| Screenshots | - | Playwright MCP |

### Test Environment

- **Docker Compose test profile**: Isolated services for testing
- **Test database**: Separate PostgreSQL schema or database
- **Test OpenSearch index**: Prefixed with `test_`
- **Test data directory**: `/data/test/`

---

## 2. Test Resources

### 2.1 Test Video Source: YouTube Video

We use a real YouTube video with its associated transcript as our primary test resource. This provides:
- Real-world audio with natural speech patterns
- Multiple speakers for diarization testing
- Ground truth transcript from YouTube captions
- Technical content matching the project's use case

#### Primary Test Video

| Property | Value |
|----------|-------|
| **Source** | YouTube video (user-provided) |
| **Local filename** | `test_meeting_primary.mkv` |
| **Location** | `/data/test/videos/test_meeting_primary.mkv` |
| **Requirements** | 2+ speakers, 1-10 minutes, clear English audio |

#### Video Download Process

```bash
# Download video using yt-dlp
yt-dlp -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]" \
  --merge-output-format mkv \
  -o "/data/test/videos/test_meeting_primary.mkv" \
  "<YOUTUBE_URL>"

# Download auto-generated subtitles
yt-dlp --write-auto-sub --sub-lang en --skip-download \
  -o "/data/test/expected/test_meeting_primary" \
  "<YOUTUBE_URL>"
```

#### Ground Truth Transcript Preparation

The YouTube transcript (VTT/SRT format) is converted to our expected JSON format:

**Location**: `/data/test/expected/test_meeting_primary_ground_truth.json`

```json
{
  "source": "youtube",
  "video_id": "<YOUTUBE_VIDEO_ID>",
  "duration_seconds": 300,
  "speaker_count": 2,
  "segments": [
    {
      "start": 0.0,
      "end": 5.2,
      "text": "Welcome everyone to today's technical discussion."
    },
    {
      "start": 5.2,
      "end": 12.8,
      "text": "We'll be covering the migration from the legacy system."
    }
  ],
  "key_terms": ["migration", "legacy", "system"],
  "expected_topics": ["technical discussion", "system migration"],
  "language": "en"
}
```

**Note**: YouTube transcripts don't include speaker labels. Speaker diarization accuracy is verified by checking speaker count and that speaker changes occur at reasonable boundaries.

### 2.2 Additional Test Resources

#### Resource: `test_silent.mkv`
- **Duration**: 10 seconds
- **Content**: Video with silent audio track
- **Purpose**: Edge case - verify graceful handling of no speech
- **Creation**: `ffmpeg -f lavfi -i anullsrc=r=44100:cl=stereo -f lavfi -i color=c=black:s=640x480 -t 10 -c:v libx264 -c:a aac test_silent.mkv`
- **Location**: `/data/test/videos/test_silent.mkv`

#### Resource: `test_corrupted.mkv`
- **Content**: Truncated/invalid video file
- **Purpose**: Error handling verification
- **Creation**: `head -c 1000 test_meeting_primary.mkv > test_corrupted.mkv`
- **Location**: `/data/test/videos/test_corrupted.mkv`

### 2.3 LLM-Based Transcript Verification

Since WhisperX transcription is non-deterministic, we use an LLM agent to perform fuzzy comparison between the generated transcript and the ground truth.

#### Verification Flow

```
┌─────────────────────────────┐     ┌─────────────────────────────┐
│  WhisperX Generated         │     │  YouTube Ground Truth       │
│  Transcript                 │     │  Transcript                 │
│  /data/transcripts/{id}.json│     │  /data/test/expected/*.json │
└─────────────┬───────────────┘     └─────────────┬───────────────┘
              │                                   │
              └───────────────┬───────────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │     LLM Verification Agent    │
              │                               │
              │  Reads both files and         │
              │  evaluates against criteria   │
              └───────────────┬───────────────┘
                              │
                              ▼
              ┌───────────────────────────────┐
              │     Verification Report       │
              │                               │
              │  - content_accuracy: PASS/FAIL│
              │  - speaker_diarization: PASS  │
              │  - timestamp_alignment: PASS  │
              │  - key_terms_preserved: PASS  │
              │  - overall: PASS/FAIL         │
              └───────────────────────────────┘
```

#### LLM Verification Prompt

The verification agent uses the following prompt template:

```
READ FILE: /data/transcripts/{video_id}.json
READ FILE: /data/test/expected/test_meeting_primary_ground_truth.json

You are a transcript verification agent. Compare the generated transcript
against the ground truth and evaluate the following criteria:

## Evaluation Criteria

### 1. Content Accuracy (Weight: 40%)
- Are the same statements and ideas captured?
- Is the overall meaning preserved?
- Minor word variations are acceptable (e.g., "gonna" vs "going to")
- Threshold: >85% semantic similarity

### 2. Speaker Diarization (Weight: 20%)
- Does the number of distinct speakers match expectations?
- Do speaker transitions occur at reasonable boundaries?
- Note: Speaker labels (SPEAKER_00 vs SPEAKER_01) may differ from ground truth
- Threshold: Speaker count matches, transitions within ±3 seconds

### 3. Timestamp Alignment (Weight: 20%)
- Are segment timestamps within acceptable tolerance?
- Tolerance: ±2 seconds for segment boundaries
- Overall duration should match within ±5 seconds

### 4. Key Terms Preservation (Weight: 20%)
- Are technical terms, names, and domain-specific words captured?
- Check against the key_terms list in ground truth
- Threshold: >90% of key terms present

## Output Format

VERIFICATION_RESULT|{overall_pass}|{content_score}|{speaker_score}|{timestamp_score}|{terms_score}
CONTENT_ACCURACY|{PASS/FAIL}|{details}
SPEAKER_DIARIZATION|{PASS/FAIL}|{details}
TIMESTAMP_ALIGNMENT|{PASS/FAIL}|{details}
KEY_TERMS|{PASS/FAIL}|{missing_terms}
SUMMARY|{brief explanation}
```

#### Verification Thresholds

| Criterion | Pass Threshold | Weight |
|-----------|---------------|--------|
| Content Accuracy | >85% semantic match | 40% |
| Speaker Diarization | Count matches, transitions ±3s | 20% |
| Timestamp Alignment | Boundaries ±2s, duration ±5s | 20% |
| Key Terms Preserved | >90% terms found | 20% |
| **Overall Pass** | Weighted score ≥80% | - |

### 2.4 Test Search Queries and Expected Results

Based on the actual content of the test video, define search queries:

| Query Type | Example Query | Expected Behavior | Verification |
|------------|---------------|-------------------|--------------|
| Exact keyword | "[key term from video]" | Returns matching segment | Segment contains term |
| Semantic search | "How does [topic] work?" | Returns relevant segment | LLM confirms relevance |
| Multi-word phrase | "[phrase from transcript]" | Returns exact segment | High confidence match |
| No results | "xyznonexistent123" | Empty results | Results array empty |

**Note**: Specific queries are defined after the test video is selected, based on its actual content.

### 2.5 Test Data Preparation Script

Location: `/scripts/prepare-test-data.sh`

```bash
#!/bin/bash
# Prepares test data from a YouTube video
#
# Usage: ./scripts/prepare-test-data.sh <YOUTUBE_URL>
#
# This script:
# 1. Downloads the video as MKV
# 2. Downloads YouTube's auto-generated transcript
# 3. Converts transcript to ground truth JSON format
# 4. Creates edge-case test files (silent, corrupted)
# 5. Extracts key terms for search testing

set -e

YOUTUBE_URL="$1"
TEST_DATA_DIR="/data/test"
VIDEOS_DIR="${TEST_DATA_DIR}/videos"
EXPECTED_DIR="${TEST_DATA_DIR}/expected"

# Create directories
mkdir -p "$VIDEOS_DIR" "$EXPECTED_DIR"

# Download video
echo "Downloading video..."
yt-dlp -f "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]" \
  --merge-output-format mkv \
  -o "${VIDEOS_DIR}/test_meeting_primary.mkv" \
  "$YOUTUBE_URL"

# Download subtitles
echo "Downloading subtitles..."
yt-dlp --write-auto-sub --sub-lang en --skip-download \
  --convert-subs srt \
  -o "${EXPECTED_DIR}/test_meeting_primary" \
  "$YOUTUBE_URL"

# Convert SRT to ground truth JSON (using Python helper)
echo "Converting to ground truth format..."
python3 scripts/convert_srt_to_ground_truth.py \
  "${EXPECTED_DIR}/test_meeting_primary.en.srt" \
  "${EXPECTED_DIR}/test_meeting_primary_ground_truth.json"

# Create silent test video
echo "Creating silent test video..."
ffmpeg -y -f lavfi -i anullsrc=r=44100:cl=stereo \
  -f lavfi -i color=c=black:s=640x480 \
  -t 10 -c:v libx264 -c:a aac \
  "${VIDEOS_DIR}/test_silent.mkv"

# Create corrupted test file
echo "Creating corrupted test file..."
head -c 1000 "${VIDEOS_DIR}/test_meeting_primary.mkv" > "${VIDEOS_DIR}/test_corrupted.mkv"

echo "Test data preparation complete!"
echo "Files created:"
ls -la "$VIDEOS_DIR"
ls -la "$EXPECTED_DIR"
```

### 2.6 SRT to Ground Truth Converter

Location: `/scripts/convert_srt_to_ground_truth.py`

```python
#!/usr/bin/env python3
"""
Converts SRT subtitle file to ground truth JSON format.

Usage: python convert_srt_to_ground_truth.py input.srt output.json
"""

import json
import re
import sys
from pathlib import Path


def parse_srt_timestamp(ts: str) -> float:
    """Convert SRT timestamp (HH:MM:SS,mmm) to seconds."""
    match = re.match(r'(\d+):(\d+):(\d+),(\d+)', ts)
    if not match:
        raise ValueError(f"Invalid timestamp: {ts}")
    h, m, s, ms = map(int, match.groups())
    return h * 3600 + m * 60 + s + ms / 1000


def parse_srt(srt_path: Path) -> list[dict]:
    """Parse SRT file into segments."""
    content = srt_path.read_text(encoding='utf-8')
    segments = []

    # SRT format: index, timestamp line, text, blank line
    blocks = content.strip().split('\n\n')

    for block in blocks:
        lines = block.strip().split('\n')
        if len(lines) < 3:
            continue

        # Parse timestamp line: "00:00:01,000 --> 00:00:05,200"
        ts_match = re.match(
            r'(\d+:\d+:\d+,\d+)\s*-->\s*(\d+:\d+:\d+,\d+)',
            lines[1]
        )
        if not ts_match:
            continue

        start = parse_srt_timestamp(ts_match.group(1))
        end = parse_srt_timestamp(ts_match.group(2))
        text = ' '.join(lines[2:]).strip()

        # Clean up text (remove HTML tags, etc.)
        text = re.sub(r'<[^>]+>', '', text)

        segments.append({
            'start': round(start, 2),
            'end': round(end, 2),
            'text': text
        })

    return segments


def extract_key_terms(segments: list[dict]) -> list[str]:
    """Extract potential key terms from transcript."""
    # Combine all text
    full_text = ' '.join(seg['text'] for seg in segments)

    # Simple extraction: words that appear capitalized mid-sentence
    # or technical-looking terms (contains numbers, camelCase, etc.)
    words = re.findall(r'\b[A-Z][a-z]+(?:\s+[A-Z][a-z]+)*\b', full_text)

    # Deduplicate and filter common words
    common_words = {'The', 'This', 'That', 'When', 'Where', 'What', 'How', 'Why'}
    key_terms = list(set(w for w in words if w not in common_words))

    return key_terms[:20]  # Limit to top 20


def main():
    if len(sys.argv) != 3:
        print("Usage: python convert_srt_to_ground_truth.py input.srt output.json")
        sys.exit(1)

    srt_path = Path(sys.argv[1])
    output_path = Path(sys.argv[2])

    segments = parse_srt(srt_path)

    if not segments:
        print("Error: No segments parsed from SRT file")
        sys.exit(1)

    # Calculate metadata
    duration = segments[-1]['end'] if segments else 0
    word_count = sum(len(seg['text'].split()) for seg in segments)
    key_terms = extract_key_terms(segments)

    ground_truth = {
        'source': 'youtube',
        'source_file': srt_path.name,
        'duration_seconds': round(duration, 2),
        'segment_count': len(segments),
        'word_count': word_count,
        'segments': segments,
        'key_terms': key_terms,
        'language': 'en',
        'notes': 'Auto-generated from YouTube captions. Speaker labels not available.'
    }

    output_path.write_text(
        json.dumps(ground_truth, indent=2, ensure_ascii=False),
        encoding='utf-8'
    )

    print(f"Created ground truth file: {output_path}")
    print(f"  - Duration: {duration:.1f}s")
    print(f"  - Segments: {len(segments)}")
    print(f"  - Words: {word_count}")
    print(f"  - Key terms: {len(key_terms)}")


if __name__ == '__main__':
    main()
```

---

## 3. Story-by-Story Test Specifications

### V1: Video Upload

#### Acceptance Criteria
- Upload form accepts MKV files
- Progress indicator during upload
- Can add title, date, participant names, and context notes

#### Unit Tests (Backend)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| V1-U01 | `test_video_schema_validation` | Validate VideoCreate schema | Valid data passes, invalid rejected |
| V1-U02 | `test_video_file_extension_validation` | Only .mkv files accepted | Non-MKV rejected with 400 |
| V1-U03 | `test_video_metadata_required_fields` | Title and date are required | Missing fields return 422 |
| V1-U04 | `test_participants_array_parsing` | Participants parsed as array | ["Alice", "Bob"] stored correctly |

#### Integration Tests (Backend)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| V1-I01 | `test_upload_creates_video_record` | POST /videos creates DB record | Video in DB with status='uploaded' |
| V1-I02 | `test_upload_stores_file` | File saved to /data/videos/original/ | File exists at expected path |
| V1-I03 | `test_upload_triggers_processing_task` | Celery task queued after upload | Task visible in Celery |
| V1-I04 | `test_upload_returns_video_id` | Response includes video UUID | Valid UUID returned |

#### Frontend Unit Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| V1-F01 | `test_upload_form_renders` | UploadForm component renders | All fields visible |
| V1-F02 | `test_upload_form_validation` | Client-side validation | Error shown for missing title |
| V1-F03 | `test_file_type_restriction` | Only MKV selectable | File input accepts .mkv |
| V1-F04 | `test_upload_progress_display` | Progress shown during upload | Progress bar updates |

---

### V2: Automatic Transcription

#### Acceptance Criteria
- Transcription generated automatically
- Timestamps preserved for each segment
- Handles accented English (European, African, Indian speakers)

#### Unit Tests (Backend)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| V2-U01 | `test_whisperx_output_parsing` | Parse WhisperX JSON output | Segments extracted correctly |
| V2-U02 | `test_segment_timestamp_extraction` | Start/end times parsed | Float values in seconds |
| V2-U03 | `test_speaker_label_extraction` | Speaker labels captured | "SPEAKER_00" format preserved |
| V2-U04 | `test_word_count_calculation` | Word count computed | Matches expected count |

#### Integration Tests (Backend)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| V2-I01 | `test_transcription_creates_transcript_record` | Transcript row created | transcript.video_id matches |
| V2-I02 | `test_transcription_creates_segments` | Segments created in DB | Count matches WhisperX output |
| V2-I03 | `test_audio_extraction` | WAV extracted from MKV | Audio file exists temporarily |
| V2-I04 | `test_transcription_with_test_video` | Full pipeline with test video | Transcript matches expected output |
| V2-I05 | `test_thumbnail_generated` | Thumbnail created during processing | File exists at thumbnail_path |

#### E2E Tests (Transcription Quality - LLM Verified)

These tests use the LLM verification agent to compare WhisperX output against the YouTube ground truth transcript.

| Test ID | Test Name | Description | LLM Verification Criteria |
|---------|-----------|-------------|---------------------------|
| V2-E01 | `test_transcription_content_accuracy` | Compare semantic content | Content Accuracy ≥85% |
| V2-E02 | `test_speaker_diarization` | Verify speaker separation | Speaker count matches, transitions reasonable |
| V2-E03 | `test_timestamp_alignment` | Verify timing accuracy | Segment boundaries within ±2s |
| V2-E04 | `test_key_terms_preserved` | Technical terms captured | ≥90% of key terms found |
| V2-E05 | `test_overall_transcription_quality` | Combined quality check | Weighted score ≥80% |

**LLM Verification Implementation**:

```python
# backend/tests/e2e/test_transcription_quality.py

import subprocess
import json
from pathlib import Path

def run_llm_verification(video_id: str) -> dict:
    """Run LLM agent to verify transcription quality."""

    prompt = f"""
READ FILE: /data/transcripts/{video_id}.json
READ FILE: /data/test/expected/test_meeting_primary_ground_truth.json

Compare the generated transcript against the ground truth using these criteria:

1. CONTENT_ACCURACY: Are the same ideas captured? (threshold: >85% semantic match)
2. SPEAKER_DIARIZATION: Does speaker count match? Transitions reasonable? (±3s tolerance)
3. TIMESTAMP_ALIGNMENT: Are boundaries within ±2 seconds?
4. KEY_TERMS: Are >90% of key_terms from ground truth present?

Output EXACTLY in this format:
VERIFICATION_RESULT|{{overall_pass: true/false}}|{{weighted_score: 0-100}}
CONTENT_ACCURACY|{{PASS/FAIL}}|{{score: 0-100}}|{{details}}
SPEAKER_DIARIZATION|{{PASS/FAIL}}|{{score: 0-100}}|{{details}}
TIMESTAMP_ALIGNMENT|{{PASS/FAIL}}|{{score: 0-100}}|{{details}}
KEY_TERMS|{{PASS/FAIL}}|{{score: 0-100}}|{{missing_terms}}
"""

    result = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True,
        text=True,
        cwd="/home/ubuntu/code/whedifaqaui"
    )

    return parse_verification_output(result.stdout)


def test_overall_transcription_quality():
    """E2E test: Verify transcription meets quality thresholds."""
    # Assumes video has been uploaded and processed
    video_id = get_test_video_id()

    verification = run_llm_verification(video_id)

    assert verification['overall_pass'] == True
    assert verification['weighted_score'] >= 80
    assert verification['content_accuracy']['pass'] == True
    assert verification['key_terms']['pass'] == True
```

---

### V3: Processing Status

#### Acceptance Criteria
- Status indicators: uploading, transcribing, analyzing, ready
- Notification/indication when complete

#### Unit Tests (Backend)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| V3-U01 | `test_status_enum_values` | Valid status values | All expected statuses defined |
| V3-U02 | `test_status_transition_validation` | Invalid transitions rejected | Cannot go from 'ready' to 'uploaded' |

#### Integration Tests (Backend)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| V3-I01 | `test_status_updates_during_processing` | Status changes tracked | uploaded→processing→transcribing→... |
| V3-I02 | `test_status_endpoint_returns_current` | GET /videos/{id}/status | Returns current status |
| V3-I03 | `test_error_status_with_message` | Error captured with message | status='error', error_message set |

#### Frontend Unit Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| V3-F01 | `test_status_badge_colors` | Different colors per status | Each status has distinct color |
| V3-F02 | `test_status_polling` | Status auto-refreshes | Polls every 5 seconds |
| V3-F03 | `test_ready_notification` | UI indicates when ready | Badge changes to 'Ready' |

---

### C1: Semantic Chunking

#### Acceptance Criteria
- Transcript segmented into semantic chunks for search indexing
- Chunks preserve speaker attribution
- Chunks have appropriate size for embedding

#### Unit Tests (Backend)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| C1-U01 | `test_chunk_size_limits` | Chunks within size bounds | 50-500 words per chunk |
| C1-U02 | `test_chunk_preserves_speaker` | Speaker label retained | Each chunk has speaker field |
| C1-U03 | `test_chunk_timestamps_valid` | Start/end times logical | start_time < end_time |
| C1-U04 | `test_semantic_boundary_detection` | Splits at natural breaks | Chunks end at sentence boundaries |

#### Integration Tests (Backend)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| C1-I01 | `test_chunking_creates_segments` | Segments stored in DB | segment_count > 0 |
| C1-I02 | `test_chunks_indexed_to_opensearch` | Segments indexed | OpenSearch doc count matches DB |
| C1-I03 | `test_chunk_embeddings_generated` | Embeddings computed | 768-dim vector per segment |

---

### P1: Embedded Video Player

#### Acceptance Criteria
- Embedded video player
- Standard controls (play, pause, seek, volume)
- Supports MKV format (via transcoded MP4)

#### Unit Tests (Backend)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| P1-U01 | `test_video_transcode_to_mp4` | FFmpeg transcodes MKV→MP4 | MP4 file created |
| P1-U02 | `test_processed_path_stored` | processed_path saved | DB record updated |

#### Integration Tests (Backend)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| P1-I01 | `test_stream_endpoint_returns_video` | GET /videos/{id}/stream | Returns video bytes |
| P1-I02 | `test_stream_supports_range_requests` | Range header support | 206 Partial Content |
| P1-I03 | `test_stream_content_type` | Correct MIME type | video/mp4 |

#### Frontend Unit Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| P1-F01 | `test_video_player_renders` | VideoPlayer component loads | <video> element present |
| P1-F02 | `test_player_controls_visible` | Controls displayed | Play, pause, seek, volume visible |
| P1-F03 | `test_player_loads_source` | Video source set correctly | src points to stream endpoint |

---

### P2: Timestamp Navigation

#### Acceptance Criteria
- Clickable timestamps throughout interface
- URL deep-linking to timestamp (shareable)

#### Unit Tests (Backend)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| P2-U01 | `test_timestamp_formatting` | Seconds to MM:SS format | 125 → "2:05" |
| P2-U02 | `test_timestamp_parsing` | MM:SS to seconds | "2:05" → 125 |

#### Frontend Unit Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| P2-F01 | `test_timestamp_link_renders` | TimestampLink displays time | "1:23" visible |
| P2-F02 | `test_timestamp_click_seeks_video` | Click jumps to time | Player.currentTime = 83 |
| P2-F03 | `test_url_with_timestamp` | URL includes ?t=seconds | /videos/123?t=83 |
| P2-F04 | `test_url_timestamp_auto_seeks` | Page load with ?t seeks | Player seeks on mount |

---

### P3: Synchronized Transcript

#### Acceptance Criteria
- Synchronized transcript display
- Current segment highlighted
- Click transcript to jump to that moment

#### Integration Tests (Backend)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| P3-I01 | `test_transcript_endpoint_returns_segments` | GET /videos/{id}/transcript | Segments with timestamps |
| P3-I02 | `test_transcript_includes_speaker` | Speaker labels in response | speaker field present |

#### Frontend Unit Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| P3-F01 | `test_transcript_panel_renders` | TranscriptPanel displays | Segments listed |
| P3-F02 | `test_current_segment_highlighted` | Active segment styled | CSS class 'active' applied |
| P3-F03 | `test_segment_click_seeks` | Click segment jumps video | Player seeks to start_time |
| P3-F04 | `test_auto_scroll_to_current` | Panel scrolls during playback | Active segment in view |
| P3-F05 | `test_speaker_labels_displayed` | Speaker shown per segment | "SPEAKER_00:" prefix |

---

### S1: Natural Language Search

#### Acceptance Criteria
- Free-text query input
- System interprets intent (not just keyword matching)
- Handles conceptual questions ("How does X work?")

#### Unit Tests (Backend)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| S1-U01 | `test_embedding_generation` | BGE model generates embeddings | 768-dim vector returned |
| S1-U02 | `test_hybrid_query_construction` | BM25 + kNN query built | Both clauses present |
| S1-U03 | `test_search_result_ranking` | Results sorted by score | Highest score first |
| S1-U04 | `test_empty_query_handled` | Empty string query | Returns empty or error |

#### Integration Tests (Backend)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| S1-I01 | `test_search_finds_keyword_match` | Query "authentication" | Matching segment returned |
| S1-I02 | `test_search_finds_semantic_match` | Query "how do tokens expire" | OAuth segment returned |
| S1-I03 | `test_search_no_results` | Query "nonexistent xyz" | Empty results array |
| S1-I04 | `test_search_across_videos` | Multi-video search | Results from multiple videos |
| S1-I05 | `test_opensearch_index_mapping` | Index has correct schema | kNN enabled, 768-dim vector field, text analyzer |

#### Frontend Unit Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| S1-F01 | `test_search_bar_renders` | SearchBar component | Input field present |
| S1-F02 | `test_search_submits_query` | Enter key submits | API called with query |
| S1-F03 | `test_search_loading_state` | Loading indicator | Spinner during search |

---

### S3: Timestamp Links in Results

#### Acceptance Criteria
- Each citation includes clickable timestamp
- Click navigates to that moment in video player

#### Integration Tests (Backend)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| S3-I01 | `test_search_results_include_timestamps` | start_time in response | Float value present |
| S3-I02 | `test_search_results_include_video_id` | video_id in response | UUID present |

#### Frontend Unit Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| S3-F01 | `test_search_result_shows_timestamp` | Timestamp displayed | "at 1:23" visible |
| S3-F02 | `test_search_result_link_navigates` | Click navigates | Router pushes /videos/{id}?t= |

---

### M1: Video Library View

#### Acceptance Criteria
- Video library view
- Sortable/filterable by date, status, topic
- Quick access to edit metadata

#### Integration Tests (Backend)

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| M1-I01 | `test_list_videos_returns_all` | GET /videos | All videos returned |
| M1-I02 | `test_list_videos_pagination` | limit/offset params | Paginated results |
| M1-I03 | `test_list_videos_filter_by_status` | ?status=ready | Only ready videos |
| M1-I04 | `test_list_videos_sort_by_date` | ?sort=recording_date | Ordered by date |

#### Frontend Unit Tests

| Test ID | Test Name | Description | Expected Result |
|---------|-----------|-------------|-----------------|
| M1-F01 | `test_library_page_renders` | LibraryPage loads | Video list displayed |
| M1-F02 | `test_video_card_displays_metadata` | VideoCard shows info | Title, date, status visible |
| M1-F03 | `test_filter_controls_present` | Filter dropdowns | Status, date filters |
| M1-F04 | `test_sort_controls_present` | Sort buttons | Sort by date option |
| M1-F05 | `test_thumbnail_displayed` | Thumbnail image | <img> with thumbnail src |

---

## 4. End-to-End Test Scenarios

### E2E-01: Complete Upload-to-Search Flow

**Preconditions**: System running, no videos in database, test data prepared

**Test Video**: `test_meeting_primary.mkv` (YouTube-sourced)

**Steps**:
1. Navigate to Upload page
2. Select `test_meeting_primary.mkv`
3. Enter metadata:
   - Title: "Test Technical Meeting"
   - Date: (use video's actual date)
   - Participants: (based on video content)
   - Notes: "Phase 1 E2E test video"
4. Click Upload
5. Wait for processing to complete (status = ready)
6. **LLM Verification**: Run transcript quality verification against ground truth
7. Navigate to Search page
8. Search for a key term from the ground truth
9. Verify result shows the uploaded video
10. Click timestamp link
11. Verify video player loads and seeks to correct position
12. Verify transcript is synchronized

**Expected Results**:
- Video uploaded successfully
- Processing completes within reasonable time
- **LLM verification passes** (weighted score ≥80%)
- Search returns the uploaded video for key terms
- Timestamp navigation works
- Transcript displays with speaker labels

**LLM Verification Step** (Step 6):
```python
# Automated verification after processing completes
verification = run_llm_verification(video_id)
assert verification['overall_pass'] == True, f"Transcript quality failed: {verification}"
```

**Playwright Screenshots**:
- `e2e01-01-upload-form.png` - Empty upload form
- `e2e01-02-form-filled.png` - Form with metadata entered
- `e2e01-03-upload-progress.png` - Upload in progress
- `e2e01-04-processing-status.png` - Status showing processing
- `e2e01-05-ready-status.png` - Status showing ready
- `e2e01-06-search-results.png` - Search results page
- `e2e01-07-video-player.png` - Video player with transcript

---

### E2E-02: Video Playback with Transcript Sync

**Preconditions**: `test_meeting_primary` video already processed

**Steps**:
1. Navigate to Library page
2. Click on "Test Technical Meeting" video
3. Verify player loads
4. Play video
5. Observe transcript highlighting updates
6. Click on third segment in transcript
7. Verify video seeks to that timestamp
8. Verify URL updates with timestamp parameter
9. Copy URL and open in new tab
10. Verify video loads at correct timestamp

**Expected Results**:
- Transcript syncs with video playback
- Clicking transcript seeks video
- URL deep-linking works

**Playwright Screenshots**:
- `e2e02-01-library-view.png` - Library with test video
- `e2e02-02-player-initial.png` - Player at start
- `e2e02-03-transcript-highlight.png` - Highlighted segment during playback
- `e2e02-04-after-seek.png` - After clicking transcript segment
- `e2e02-05-deep-link-load.png` - Page loaded from deep link

---

### E2E-03: Library Filtering and Status Display

**Preconditions**: Multiple videos in various states

**Setup**:
- Video A: status=ready, date=2024-01-01
- Video B: status=processing, date=2024-02-01
- Video C: status=ready, date=2024-03-01

**Steps**:
1. Navigate to Library page
2. Verify all videos visible
3. Filter by status=ready
4. Verify only A and C visible
5. Sort by date descending
6. Verify order: C, A
7. Clear filters
8. Verify B shows processing indicator

**Expected Results**:
- Filtering works correctly
- Sorting works correctly
- Status indicators accurate

**Playwright Screenshots**:
- `e2e03-01-all-videos.png` - Unfiltered library
- `e2e03-02-filtered-ready.png` - Filtered to ready only
- `e2e03-03-sorted-date-desc.png` - Sorted by date
- `e2e03-04-processing-indicator.png` - Processing status visible

---

### E2E-04: Search with No Results

**Preconditions**: Test video processed

**Steps**:
1. Navigate to Search page
2. Search for "nonexistent term xyz123"
3. Verify no results message displayed
4. Search for "" (empty)
5. Verify appropriate handling

**Expected Results**:
- No results gracefully handled
- Empty query handled

**Playwright Screenshots**:
- `e2e04-01-no-results.png` - No results message

---

### E2E-05: Error Handling - Corrupted Video

**Preconditions**: System running

**Steps**:
1. Navigate to Upload page
2. Upload `test_corrupted.mkv`
3. Enter valid metadata
4. Submit
5. Wait for processing
6. Verify status shows error
7. Verify error message is descriptive

**Expected Results**:
- Error status displayed
- Error message explains issue
- System remains stable

**Playwright Screenshots**:
- `e2e05-01-error-status.png` - Error status with message

---

### E2E-06: LLM Transcript Verification

**Purpose**: Dedicated test to verify transcription quality using LLM agent comparison

**Preconditions**:
- `test_meeting_primary.mkv` uploaded and processed to `ready` status
- Ground truth transcript available at `/data/test/expected/test_meeting_primary_ground_truth.json`

**Steps**:
1. Retrieve the generated transcript for the test video
2. Load the ground truth transcript
3. Invoke LLM verification agent with both transcripts
4. Parse verification output
5. Assert all criteria pass

**Verification Criteria**:

| Criterion | Threshold | Weight | Description |
|-----------|-----------|--------|-------------|
| Content Accuracy | ≥85% | 40% | Semantic similarity of content |
| Speaker Diarization | Pass | 20% | Speaker count and transition timing |
| Timestamp Alignment | ±2s | 20% | Segment boundary accuracy |
| Key Terms | ≥90% | 20% | Technical terms preserved |
| **Overall** | ≥80% | - | Weighted combination |

**Test Implementation**:

```python
# backend/tests/e2e/test_llm_transcript_verification.py

import pytest
from tests.utils.llm_verification import run_llm_verification, parse_verification_output

@pytest.fixture
def processed_test_video(test_db, celery_worker):
    """Upload and process test video, wait for completion."""
    video_id = upload_test_video("test_meeting_primary.mkv")
    wait_for_status(video_id, "ready", timeout=300)
    return video_id


def test_transcript_content_accuracy(processed_test_video):
    """V2-E01: Verify semantic content matches ground truth."""
    verification = run_llm_verification(processed_test_video)

    assert verification['content_accuracy']['pass'] == True
    assert verification['content_accuracy']['score'] >= 85


def test_speaker_diarization(processed_test_video):
    """V2-E02: Verify speaker separation is reasonable."""
    verification = run_llm_verification(processed_test_video)

    assert verification['speaker_diarization']['pass'] == True


def test_timestamp_alignment(processed_test_video):
    """V2-E03: Verify timestamps align with ground truth."""
    verification = run_llm_verification(processed_test_video)

    assert verification['timestamp_alignment']['pass'] == True


def test_key_terms_preserved(processed_test_video):
    """V2-E04: Verify technical terms are captured."""
    verification = run_llm_verification(processed_test_video)

    assert verification['key_terms']['pass'] == True
    assert verification['key_terms']['score'] >= 90


def test_overall_quality(processed_test_video):
    """V2-E05: Verify overall weighted quality score."""
    verification = run_llm_verification(processed_test_video)

    assert verification['overall_pass'] == True
    assert verification['weighted_score'] >= 80
```

**LLM Verification Utility Module**:

```python
# backend/tests/utils/llm_verification.py

import subprocess
import re
from pathlib import Path

VERIFICATION_PROMPT_TEMPLATE = """
READ FILE: {transcript_path}
READ FILE: {ground_truth_path}

You are a transcript verification agent. Compare the WhisperX-generated transcript
against the YouTube ground truth transcript.

## Evaluation Criteria

### 1. Content Accuracy (Weight: 40%)
Compare the semantic content of both transcripts:
- Are the same statements, ideas, and information captured?
- Minor word variations are acceptable ("gonna" vs "going to", "wanna" vs "want to")
- Filler words may differ (um, uh, like)
- Score 0-100 based on semantic overlap

### 2. Speaker Diarization (Weight: 20%)
Note: YouTube transcripts don't have speaker labels, so evaluate:
- Does the generated transcript identify multiple speakers if the audio has multiple speakers?
- Do speaker transitions occur at reasonable points (pauses, turn-taking)?
- Score: PASS if speaker handling is reasonable, FAIL if clearly wrong

### 3. Timestamp Alignment (Weight: 20%)
Compare segment timestamps:
- Are segment start/end times within ±2 seconds of ground truth?
- Is the total duration within ±5 seconds?
- Score based on percentage of aligned segments

### 4. Key Terms Preservation (Weight: 20%)
Check the key_terms list from ground truth:
- What percentage of key terms appear in the generated transcript?
- Technical terms, names, and domain-specific words are critical
- Score 0-100 based on percentage found

## Output Format (EXACT FORMAT REQUIRED)

VERIFICATION_RESULT|{{overall_pass}}|{{weighted_score}}
CONTENT_ACCURACY|{{PASS/FAIL}}|{{score}}|{{brief_explanation}}
SPEAKER_DIARIZATION|{{PASS/FAIL}}|{{score}}|{{brief_explanation}}
TIMESTAMP_ALIGNMENT|{{PASS/FAIL}}|{{score}}|{{brief_explanation}}
KEY_TERMS|{{PASS/FAIL}}|{{score}}|{{missing_terms_if_any}}
SUMMARY|{{one_sentence_summary}}

Example output:
VERIFICATION_RESULT|true|87
CONTENT_ACCURACY|PASS|92|Captured all main discussion points with minor word variations
SPEAKER_DIARIZATION|PASS|85|Correctly identified 2 speakers with reasonable transitions
TIMESTAMP_ALIGNMENT|PASS|88|Most segments within tolerance, slight drift at end
KEY_TERMS|PASS|95|Found 19/20 key terms, missing: "OAuth"
SUMMARY|Transcription quality is good with 87% weighted score
"""


def run_llm_verification(video_id: str) -> dict:
    """
    Run LLM agent to verify transcript against ground truth.

    Returns dict with verification results.
    """
    transcript_path = f"/data/transcripts/{video_id}.json"
    ground_truth_path = "/data/test/expected/test_meeting_primary_ground_truth.json"

    prompt = VERIFICATION_PROMPT_TEMPLATE.format(
        transcript_path=transcript_path,
        ground_truth_path=ground_truth_path
    )

    result = subprocess.run(
        ["claude", "-p", prompt],
        capture_output=True,
        text=True,
        cwd="/home/ubuntu/code/whedifaqaui",
        timeout=120
    )

    if result.returncode != 0:
        raise RuntimeError(f"LLM verification failed: {result.stderr}")

    return parse_verification_output(result.stdout)


def parse_verification_output(output: str) -> dict:
    """Parse pipe-delimited verification output from LLM."""
    result = {
        'overall_pass': False,
        'weighted_score': 0,
        'content_accuracy': {'pass': False, 'score': 0, 'details': ''},
        'speaker_diarization': {'pass': False, 'score': 0, 'details': ''},
        'timestamp_alignment': {'pass': False, 'score': 0, 'details': ''},
        'key_terms': {'pass': False, 'score': 0, 'details': ''},
        'summary': ''
    }

    for line in output.strip().split('\n'):
        if not line or line.startswith('#'):
            continue

        parts = line.split('|')
        if len(parts) < 2:
            continue

        record_type = parts[0].strip()

        if record_type == 'VERIFICATION_RESULT':
            result['overall_pass'] = parts[1].strip().lower() == 'true'
            result['weighted_score'] = int(parts[2].strip())

        elif record_type == 'CONTENT_ACCURACY':
            result['content_accuracy'] = {
                'pass': parts[1].strip() == 'PASS',
                'score': int(parts[2].strip()),
                'details': parts[3].strip() if len(parts) > 3 else ''
            }

        elif record_type == 'SPEAKER_DIARIZATION':
            result['speaker_diarization'] = {
                'pass': parts[1].strip() == 'PASS',
                'score': int(parts[2].strip()),
                'details': parts[3].strip() if len(parts) > 3 else ''
            }

        elif record_type == 'TIMESTAMP_ALIGNMENT':
            result['timestamp_alignment'] = {
                'pass': parts[1].strip() == 'PASS',
                'score': int(parts[2].strip()),
                'details': parts[3].strip() if len(parts) > 3 else ''
            }

        elif record_type == 'KEY_TERMS':
            result['key_terms'] = {
                'pass': parts[1].strip() == 'PASS',
                'score': int(parts[2].strip()),
                'details': parts[3].strip() if len(parts) > 3 else ''
            }

        elif record_type == 'SUMMARY':
            result['summary'] = parts[1].strip() if len(parts) > 1 else ''

    return result
```

**Expected Output Example**:
```
VERIFICATION_RESULT|true|87
CONTENT_ACCURACY|PASS|92|All main topics captured with minor variations
SPEAKER_DIARIZATION|PASS|85|2 speakers identified, transitions at pauses
TIMESTAMP_ALIGNMENT|PASS|88|45/50 segments within ±2s tolerance
KEY_TERMS|PASS|95|19/20 terms found, missing: "OAuth"
SUMMARY|Good transcription quality meeting all thresholds
```

---

## 5. Playwright Screenshot Verification

### Screenshot Specification Format

Each screenshot verification includes:
- **ID**: Unique identifier
- **URL**: Page URL when captured
- **Wait condition**: Element to wait for before capture
- **Viewport**: Browser size
- **Assertions**: Visual elements that must be present

### Screenshot Checklist

#### Upload Flow Screenshots

| ID | Filename | Wait Condition | Assertions |
|----|----------|----------------|------------|
| SCR-U01 | `upload-form-empty.png` | `[data-testid="upload-form"]` | Title input, Date input, File input visible |
| SCR-U02 | `upload-form-filled.png` | `[data-testid="submit-btn"]` enabled | All fields populated |
| SCR-U03 | `upload-progress.png` | `[data-testid="progress-bar"]` | Progress percentage visible |
| SCR-U04 | `upload-success.png` | `[data-testid="success-message"]` | Success notification visible |

#### Library Screenshots

| ID | Filename | Wait Condition | Assertions |
|----|----------|----------------|------------|
| SCR-L01 | `library-empty.png` | `[data-testid="library-empty"]` | Empty state message |
| SCR-L02 | `library-with-videos.png` | `[data-testid="video-card"]` | Video cards visible |
| SCR-L03 | `library-status-ready.png` | `[data-testid="status-badge-ready"]` | Green ready badge |
| SCR-L04 | `library-status-processing.png` | `[data-testid="status-badge-processing"]` | Yellow processing badge |
| SCR-L05 | `library-status-error.png` | `[data-testid="status-badge-error"]` | Red error badge |

#### Video Player Screenshots

| ID | Filename | Wait Condition | Assertions |
|----|----------|----------------|------------|
| SCR-P01 | `player-loaded.png` | `video[data-testid="video-player"]` loaded | Player with controls visible |
| SCR-P02 | `player-playing.png` | Video currentTime > 0 | Progress bar moved |
| SCR-P03 | `transcript-highlighted.png` | `.transcript-segment.active` | Active segment highlighted |
| SCR-P04 | `transcript-speakers.png` | `[data-testid="speaker-label"]` | Speaker labels visible |

#### Search Screenshots

| ID | Filename | Wait Condition | Assertions |
|----|----------|----------------|------------|
| SCR-S01 | `search-empty.png` | `[data-testid="search-input"]` | Search bar visible |
| SCR-S02 | `search-loading.png` | `[data-testid="search-loading"]` | Loading spinner |
| SCR-S03 | `search-results.png` | `[data-testid="search-result"]` | Results with timestamps |
| SCR-S04 | `search-no-results.png` | `[data-testid="no-results"]` | No results message |

### Playwright Test Structure

```typescript
// e2e/phase1.spec.ts

import { test, expect } from '@playwright/test';

test.describe('Phase 1 E2E Tests', () => {

  test('E2E-01: Complete upload-to-search flow', async ({ page }) => {
    // Step 1: Navigate to upload
    await page.goto('/upload');
    await expect(page.getByTestId('upload-form')).toBeVisible();
    await page.screenshot({ path: 'screenshots/e2e01-01-upload-form.png' });

    // Step 2: Fill form
    await page.setInputFiles('[data-testid="file-input"]', 'test-data/test_meeting_short.mkv');
    await page.fill('[data-testid="title-input"]', 'Authentication Review');
    await page.fill('[data-testid="date-input"]', '2024-01-15');
    await page.fill('[data-testid="participants-input"]', 'John, Sarah');
    await page.screenshot({ path: 'screenshots/e2e01-02-form-filled.png' });

    // Step 3: Submit and wait for processing
    await page.click('[data-testid="submit-btn"]');
    await page.screenshot({ path: 'screenshots/e2e01-03-upload-progress.png' });

    // ... continue with remaining steps
  });

});
```

---

## 6. Test Data Management

### Test Database Seeding

```python
# backend/tests/fixtures/seed_data.py

TEST_VIDEOS = [
    {
        "id": "11111111-1111-1111-1111-111111111111",
        "title": "Authentication Review",
        "status": "ready",
        "recording_date": "2024-01-15",
        "duration": 30,
        "participants": ["John", "Sarah"]
    },
    {
        "id": "22222222-2222-2222-2222-222222222222",
        "title": "Database Migration Planning",
        "status": "processing",
        "recording_date": "2024-02-01",
        "duration": 120,
        "participants": ["Alice", "Bob", "Charlie"]
    }
]

TEST_SEGMENTS = [
    {
        "video_id": "11111111-1111-1111-1111-111111111111",
        "start_time": 0.0,
        "end_time": 8.0,
        "text": "Welcome to the authentication review meeting.",
        "speaker": "SPEAKER_00"
    },
    # ... additional segments
]
```

### Test Data Lifecycle

1. **Before test suite**: Seed database with known data
2. **Before each test**: Reset to known state (or use transactions)
3. **After test suite**: Clean up test data
4. **Isolation**: Each E2E test should clean up after itself

### OpenSearch Test Index

```python
# backend/tests/conftest.py

@pytest.fixture(scope="session")
def opensearch_test_index():
    """Create test index with known data."""
    index_name = "test_segments_index"
    # Create index
    # Index test documents
    yield index_name
    # Delete index
```

---

## 7. Success Criteria

### Phase 1 Completion Checklist

#### Backend Tests
- [ ] All V1-* tests passing (12 tests)
- [ ] All V2-* tests passing (9 tests)
- [ ] All V3-* tests passing (5 tests)
- [ ] All C1-* tests passing (7 tests)
- [ ] All P1-* tests passing (5 tests)
- [ ] All P2-* tests passing (2 tests)
- [ ] All P3-* tests passing (5 tests)
- [ ] All S1-* tests passing (9 tests)
- [ ] All S3-* tests passing (2 tests)
- [ ] All M1-* tests passing (4 tests)

**Total backend tests**: ~60 tests

#### Frontend Tests
- [ ] All V1-F* tests passing (4 tests)
- [ ] All V3-F* tests passing (3 tests)
- [ ] All P1-F* tests passing (3 tests)
- [ ] All P2-F* tests passing (4 tests)
- [ ] All P3-F* tests passing (5 tests)
- [ ] All S1-F* tests passing (3 tests)
- [ ] All S3-F* tests passing (2 tests)
- [ ] All M1-F* tests passing (5 tests)

**Total frontend tests**: ~29 tests

#### End-to-End Tests
- [ ] E2E-01: Upload-to-search flow passing
- [ ] E2E-02: Video playback with transcript sync passing
- [ ] E2E-03: Library filtering passing
- [ ] E2E-04: Search no results handling passing
- [ ] E2E-05: Error handling passing
- [ ] E2E-06: LLM transcript verification passing (all 5 criteria)

**Total E2E tests**: 6 scenarios

#### LLM Verification Tests (V2-E*)
- [ ] V2-E01: Content accuracy ≥85%
- [ ] V2-E02: Speaker diarization passes
- [ ] V2-E03: Timestamp alignment within ±2s
- [ ] V2-E04: Key terms ≥90% preserved
- [ ] V2-E05: Overall weighted score ≥80%

**Total LLM verification criteria**: 5 checks

#### Screenshot Verification
- [ ] All SCR-U* screenshots captured and verified
- [ ] All SCR-L* screenshots captured and verified
- [ ] All SCR-P* screenshots captured and verified
- [ ] All SCR-S* screenshots captured and verified

**Total screenshots**: ~17 screenshots

### Acceptance Verification Matrix

| Story | Unit Tests | Integration Tests | E2E Coverage | LLM Verification | Screenshots |
|-------|------------|-------------------|--------------|------------------|-------------|
| V1 | V1-U01-04, V1-F01-04 | V1-I01-04 | E2E-01 | - | SCR-U01-04 |
| V2 | V2-U01-04 | V2-I01-05 | E2E-01, E2E-06 | V2-E01 to V2-E05 | - |
| V3 | V3-U01-02, V3-F01-03 | V3-I01-03 | E2E-01, E2E-03, E2E-05 | - | SCR-L03-05 |
| C1 | C1-U01-04 | C1-I01-03 | E2E-01 | - | - |
| P1 | P1-U01-02, P1-F01-03 | P1-I01-03 | E2E-02 | - | SCR-P01-02 |
| P2 | P2-U01-02, P2-F01-04 | - | E2E-02 | - | - |
| P3 | P3-F01-05 | P3-I01-02 | E2E-02 | - | SCR-P03-04 |
| S1 | S1-U01-04, S1-F01-03 | S1-I01-05 | E2E-01, E2E-04 | - | SCR-S01-04 |
| S3 | S3-F01-02 | S3-I01-02 | E2E-01 | - | SCR-S03 |
| M1 | M1-F01-05 | M1-I01-04 | E2E-03 | - | SCR-L01-02 |

---

## Appendix A: Test File Structure

```
whedifaqaui/
├── backend/
│   └── tests/
│       ├── conftest.py           # Shared fixtures
│       ├── fixtures/
│       │   ├── seed_data.py      # Test data definitions
│       │   └── factories.py      # Model factories
│       ├── unit/
│       │   ├── test_video_schema.py
│       │   ├── test_transcription.py
│       │   ├── test_chunking.py
│       │   ├── test_embedding.py
│       │   └── test_search.py
│       ├── integration/
│       │   ├── test_video_api.py
│       │   ├── test_playback_api.py
│       │   ├── test_search_api.py
│       │   └── test_processing_pipeline.py
│       ├── e2e/
│       │   └── test_llm_transcript_verification.py  # LLM-based tests
│       └── utils/
│           └── llm_verification.py  # LLM verification utility
│
├── frontend/
│   └── src/
│       └── __tests__/
│           ├── components/
│           │   ├── VideoPlayer.test.tsx
│           │   ├── TranscriptPanel.test.tsx
│           │   ├── UploadForm.test.tsx
│           │   ├── SearchBar.test.tsx
│           │   └── VideoCard.test.tsx
│           └── pages/
│               ├── UploadPage.test.tsx
│               ├── VideoPage.test.tsx
│               ├── SearchPage.test.tsx
│               └── LibraryPage.test.tsx
│
├── e2e/
│   ├── playwright.config.ts
│   ├── phase1.spec.ts            # Playwright E2E test scenarios
│   └── screenshots/              # Captured screenshots
│
├── data/
│   └── test/
│       ├── videos/
│       │   ├── test_meeting_primary.mkv    # YouTube-sourced test video
│       │   ├── test_silent.mkv             # FFmpeg-generated silent video
│       │   └── test_corrupted.mkv          # Truncated file for error testing
│       └── expected/
│           └── test_meeting_primary_ground_truth.json  # YouTube transcript
│
└── scripts/
    ├── prepare-test-data.sh              # Downloads YouTube video + transcript
    └── convert_srt_to_ground_truth.py    # Converts SRT to ground truth JSON
```

---

## Appendix B: Commands Reference

```bash
# ============================================
# TEST DATA PREPARATION
# ============================================

# Prepare test data from YouTube video (run once)
./scripts/prepare-test-data.sh "https://www.youtube.com/watch?v=<VIDEO_ID>"

# ============================================
# BACKEND TESTS
# ============================================

# Run backend unit tests
cd backend && pytest tests/unit -v

# Run backend integration tests
cd backend && pytest tests/integration -v

# Run LLM transcript verification tests
cd backend && pytest tests/e2e/test_llm_transcript_verification.py -v

# Run all backend tests
cd backend && pytest -v

# ============================================
# FRONTEND TESTS
# ============================================

# Run frontend unit tests
cd frontend && npm run test

# Run frontend tests in watch mode
cd frontend && npm run test:watch

# ============================================
# END-TO-END TESTS (Playwright)
# ============================================

# Run E2E tests with Playwright
cd e2e && npx playwright test

# Run E2E tests with screenshot capture
cd e2e && npx playwright test --update-snapshots

# Run specific E2E test
cd e2e && npx playwright test phase1.spec.ts

# Run E2E tests with UI (debug mode)
cd e2e && npx playwright test --ui

# ============================================
# FULL TEST SUITE
# ============================================

# Run all tests (requires test data to be prepared first)
./scripts/run-all-tests.sh
```
