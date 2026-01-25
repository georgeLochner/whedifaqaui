# Search API Specification

## Overview

Whedifaqaui exposes its knowledge base through REST API endpoints. In **Deep Mode**, Claude can iteratively query these endpoints by including `curl` commands in its responses, which the backend executes and feeds back.

This enables **agentic search** where Claude decides what to search for based on the user's question, iterating until it has enough context to provide a comprehensive answer.

## Deep Mode Architecture

```
User asks question
        │
        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  Claude receives:                                                          │
│  1. User question                                                          │
│  2. System prompt with API documentation                                   │
│  3. Instructions to use CALL: curl <endpoint> for data retrieval          │
└───────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  Claude Response (iteration 1):                                            │
│  "I need to search for authentication info first.                          │
│   CALL: curl 'http://localhost:8000/api/search?query=authentication'"     │
└───────────────────────────────────────────────────────────────────────────┘
        │
        ▼ Backend parses CALL:, executes request
┌───────────────────────────────────────────────────────────────────────────┐
│  Backend feeds API response back to Claude:                                │
│  "API_RESPONSE: [{video_title: ..., timestamp: ..., text: ...}]"          │
└───────────────────────────────────────────────────────────────────────────┘
        │
        ▼
┌───────────────────────────────────────────────────────────────────────────┐
│  Claude Response (iteration 2):                                            │
│  "Found mention of Cognito. Let me get more details.                       │
│   CALL: curl 'http://localhost:8000/api/entities/cognito'"                │
└───────────────────────────────────────────────────────────────────────────┘
        │
        ▼ ... loop continues until final answer ...
┌───────────────────────────────────────────────────────────────────────────┐
│  Claude Final Response:                                                    │
│  "Based on my research, the authentication system uses AWS Cognito...      │
│   [Citation: Auth Deep Dive @ 12:34]"                                      │
└───────────────────────────────────────────────────────────────────────────┘
```

---

## Claude Context Prompt

When invoking Claude for Deep Mode, include this system context:

```
You have access to a video knowledge base API. To retrieve information,
include API calls in your response using this format:

CALL: curl '<endpoint>'

Available endpoints:

1. SEARCH - Find relevant content
   GET /api/search?query=<text>&limit=<n>&speaker=<name>&start_date=YYYY-MM-DD&end_date=YYYY-MM-DD

2. SEARCH BY SPEAKER - Find what a person said
   GET /api/search/speaker/<name>?query=<text>&limit=<n>

3. SEARCH BY DATE - Find content from a time period
   GET /api/search/date-range?start=YYYY-MM-DD&end=YYYY-MM-DD&query=<text>&limit=<n>

4. ENTITY INFO - Get details about a person, system, or project
   GET /api/entities/<name>

5. VIDEO TRANSCRIPT - Get full transcript
   GET /api/videos/<id>/transcript

6. SEGMENT CONTEXT - Expand context around a search result
   GET /api/segments/<id>/context?before=<n>&after=<n>

7. LIST VIDEOS - See available videos
   GET /api/videos?limit=<n>&sort=date_desc

8. TOPIC TIMELINE - See how a topic evolved over time
   GET /api/topics/<name>/timeline

After each CALL:, I will provide the API response. You may make multiple
calls to gather information before providing your final answer.

Always cite sources using [Video Title @ MM:SS] format.
```

---

## API Endpoints

### GET /api/search

Primary search endpoint for finding relevant content across all videos.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| query | string | Yes | - | Natural language search query |
| limit | int | No | 10 | Maximum results (max: 50) |
| speaker | string | No | - | Filter by speaker name |
| start_date | string | No | - | Filter by recording date (YYYY-MM-DD) |
| end_date | string | No | - | Filter by recording date (YYYY-MM-DD) |

**Example:**
```bash
curl 'http://localhost:8000/api/search?query=Auth0+to+Cognito+migration&limit=15'
curl 'http://localhost:8000/api/search?query=deployment+problems&speaker=John'
```

**Response:**
```json
{
  "count": 8,
  "results": [
    {
      "segment_id": "seg_abc123",
      "video_id": "vid_xyz789",
      "video_title": "Auth System Deep Dive",
      "timestamp": 754,
      "timestamp_formatted": "12:34",
      "recording_date": "2024-12-10",
      "speaker": "John",
      "text": "...so we decided to migrate from Auth0 to Cognito because of the cost implications and the better integration with our AWS stack...",
      "score": 0.92
    },
    ...
  ]
}
```

---

### GET /api/search/speaker/{name}

Find all content from a specific person.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| name | string (path) | Yes | - | Speaker name (fuzzy matching) |
| query | string | No | - | Topic to filter by |
| limit | int | No | 20 | Maximum results |

**Example:**
```bash
curl 'http://localhost:8000/api/search/speaker/John'
curl 'http://localhost:8000/api/search/speaker/John?query=database'
```

**Response:**
```json
{
  "speaker": "John",
  "total_segments": 145,
  "count": 20,
  "results": [
    {
      "segment_id": "seg_def456",
      "video_title": "Database Migration",
      "timestamp": 1234,
      "timestamp_formatted": "20:34",
      "recording_date": "2024-12-08",
      "text": "The migration plan involves three phases..."
    },
    ...
  ]
}
```

---

### GET /api/search/date-range

Find content from a specific time period.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| start | string | Yes | - | Start date (YYYY-MM-DD) |
| end | string | Yes | - | End date (YYYY-MM-DD) |
| query | string | No | - | Topic to filter by |
| limit | int | No | 20 | Maximum results |

**Example:**
```bash
curl 'http://localhost:8000/api/search/date-range?start=2024-10-01&end=2024-12-31&query=authentication'
```

**Response:**
```json
{
  "date_range": {
    "start": "2024-10-01",
    "end": "2024-12-31"
  },
  "count": 15,
  "results": [...]
}
```

---

### GET /api/entities/{name}

Get detailed information about a known entity.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| name | string (path) | Yes | Entity name (fuzzy matching) |

**Example:**
```bash
curl 'http://localhost:8000/api/entities/cognito'
curl 'http://localhost:8000/api/entities/John+Smith'
```

**Response:**
```json
{
  "entity": {
    "id": "ent_abc123",
    "name": "AWS Cognito",
    "canonical_name": "cognito",
    "type": "system",
    "description": "Authentication and user management service",
    "aliases": ["Cognito", "Amazon Cognito"],
    "first_seen": "2024-10-05",
    "last_seen": "2024-12-15",
    "mention_count": 23
  },
  "related_entities": [
    {
      "entity": {"name": "Auth0", "type": "system"},
      "relation": "migrated_from",
      "timestamp": 754,
      "video_title": "Auth System Deep Dive"
    },
    {
      "entity": {"name": "John", "type": "person"},
      "relation": "explained_by"
    }
  ],
  "videos": [
    {"video_title": "Auth System Deep Dive", "mention_count": 8, "date": "2024-12-10"},
    {"video_title": "Sprint 42 Planning", "mention_count": 5, "date": "2024-12-15"}
  ],
  "key_mentions": [
    {
      "video_title": "Auth System Deep Dive",
      "timestamp_formatted": "12:34",
      "speaker": "John",
      "text": "Cognito handles all our user authentication..."
    }
  ]
}
```

---

### GET /api/videos/{id}/transcript

Get the complete transcript of a specific video.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| id | string (path) | Yes | Video ID or title (fuzzy matching) |

**Example:**
```bash
curl 'http://localhost:8000/api/videos/vid_xyz789/transcript'
```

**Response:**
```json
{
  "video": {
    "id": "vid_xyz789",
    "title": "Auth System Deep Dive",
    "recording_date": "2024-12-10",
    "duration": 2700,
    "participants": ["John", "Sarah"]
  },
  "segments": [
    {
      "timestamp": 0,
      "timestamp_formatted": "00:00",
      "speaker": "John",
      "text": "Welcome everyone. Today we're going to do a deep dive into our authentication system."
    },
    {
      "timestamp": 15,
      "timestamp_formatted": "00:15",
      "speaker": "John",
      "text": "Let me share my screen and walk through the architecture."
    },
    ...
  ]
}
```

---

### GET /api/segments/{id}/context

Expand the context around a specific segment.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| id | string (path) | Yes | - | Segment ID |
| before | int | No | 3 | Segments to include before |
| after | int | No | 3 | Segments to include after |

**Example:**
```bash
curl 'http://localhost:8000/api/segments/seg_abc123/context?before=5&after=5'
```

**Response:**
```json
{
  "target_segment": {
    "id": "seg_abc123",
    "timestamp_formatted": "12:34",
    "text": "...the target segment..."
  },
  "context": [
    {"timestamp_formatted": "11:45", "speaker": "Sarah", "text": "...before segment 1..."},
    {"timestamp_formatted": "12:00", "speaker": "John", "text": "...before segment 2..."},
    {"timestamp_formatted": "12:34", "speaker": "John", "text": "...TARGET...", "is_target": true},
    {"timestamp_formatted": "13:00", "speaker": "Sarah", "text": "...after segment 1..."},
    {"timestamp_formatted": "13:15", "speaker": "John", "text": "...after segment 2..."}
  ]
}
```

---

### GET /api/videos

List videos in the knowledge base.

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| limit | int | No | 20 | Maximum videos to return |
| sort | string | No | date_desc | Sort order: date_desc, date_asc, title |
| status | string | No | ready | Filter: ready, all |

**Example:**
```bash
curl 'http://localhost:8000/api/videos?limit=50&sort=date_desc'
```

**Response:**
```json
{
  "count": 12,
  "videos": [
    {
      "id": "vid_abc123",
      "title": "Sprint 42 Planning",
      "recording_date": "2024-12-15",
      "duration": 4980,
      "duration_formatted": "1h 23m",
      "participants": ["John", "Sarah", "Mike"],
      "context_notes": "Discussed Q1 roadmap and technical debt priorities",
      "status": "ready"
    },
    ...
  ]
}
```

---

### GET /api/topics/{name}/timeline

Get chronological view of a topic across videos.

**Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| name | string (path) | Yes | Topic name |

**Example:**
```bash
curl 'http://localhost:8000/api/topics/authentication/timeline'
```

**Response:**
```json
{
  "topic": "authentication",
  "timeline": [
    {
      "date": "2024-10-05",
      "video_title": "Architecture Review",
      "summary": "First discussion of authentication needs",
      "key_points": ["Need to support SSO", "Considering Auth0 vs Cognito"],
      "segments": [...]
    },
    {
      "date": "2024-10-20",
      "video_title": "Sprint 38 Planning",
      "summary": "Decision to evaluate both Auth0 and Cognito",
      "key_points": ["John to do POC with both services"]
    },
    {
      "date": "2024-11-08",
      "video_title": "Auth POC Review",
      "summary": "Cognito selected over Auth0",
      "key_points": ["Better AWS integration", "Cost effective", "Lambda triggers"],
      "supersedes": "Architecture Review decisions"
    },
    ...
  ]
}
```

---

## FastAPI Implementation

```python
# backend/app/api/search.py

from fastapi import APIRouter, Query
from typing import Optional
from app.services.search import search_service
from app.services.entities import entity_service
from app.services.videos import video_service

router = APIRouter(prefix="/api", tags=["search"])


@router.get("/search")
async def search_transcripts(
    query: str,
    limit: int = Query(10, le=50),
    speaker: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None
):
    """Search video transcripts using hybrid semantic + keyword search."""
    results = await search_service.hybrid_search(
        query=query,
        limit=limit,
        filters={
            "speaker": speaker,
            "start_date": start_date,
            "end_date": end_date
        }
    )
    return {"count": len(results), "results": results}


@router.get("/search/speaker/{name}")
async def search_by_speaker(
    name: str,
    query: Optional[str] = None,
    limit: int = Query(20, le=50)
):
    """Find all segments where a specific person spoke."""
    results = await search_service.search_by_speaker(name, query, limit)
    return {
        "speaker": name,
        "total_segments": results.get("total", 0),
        "count": len(results.get("results", [])),
        "results": results.get("results", [])
    }


@router.get("/search/date-range")
async def search_by_date_range(
    start: str,
    end: str,
    query: Optional[str] = None,
    limit: int = Query(20, le=50)
):
    """Find content from videos recorded within a date range."""
    results = await search_service.search_by_date_range(start, end, query, limit)
    return {
        "date_range": {"start": start, "end": end},
        "count": len(results),
        "results": results
    }


@router.get("/entities/{name}")
async def get_entity_info(name: str):
    """Get detailed information about a specific entity."""
    entity = await entity_service.find_entity(name)
    if not entity:
        return {"error": f"Entity '{name}' not found"}

    related = await entity_service.get_related_entities(entity.id)
    videos = await entity_service.get_videos_with_entity(entity.id)
    key_mentions = await entity_service.get_key_mentions(entity.id, limit=5)

    return {
        "entity": entity,
        "related_entities": related,
        "videos": videos,
        "key_mentions": key_mentions
    }


@router.get("/videos/{video_id}/transcript")
async def get_video_transcript(video_id: str):
    """Get the full transcript of a specific video."""
    video = await video_service.get_video(video_id)
    if not video:
        return {"error": "Video not found"}

    segments = await video_service.get_transcript_segments(video.id)
    return {"video": video, "segments": segments}


@router.get("/segments/{segment_id}/context")
async def get_segment_context(
    segment_id: str,
    before: int = Query(3, le=10),
    after: int = Query(3, le=10)
):
    """Get a segment with surrounding context."""
    result = await search_service.get_segment_with_context(
        segment_id, before, after
    )
    return result


@router.get("/videos")
async def list_videos(
    limit: int = Query(20, le=100),
    sort: str = "date_desc",
    status: str = "ready"
):
    """List videos in the knowledge base."""
    videos = await video_service.list_videos(limit, sort, status)
    return {"count": len(videos), "videos": videos}


@router.get("/topics/{topic}/timeline")
async def get_topic_timeline(topic: str):
    """Get chronological timeline of a topic."""
    timeline = await search_service.get_topic_timeline(topic)
    return {"topic": topic, "timeline": timeline}
```

---

## Deep Mode Implementation

```python
# backend/app/services/deep_mode.py

import re
from app.services.claude import claude

async def deep_mode_query(user_message: str, conversation_id: str = None) -> dict:
    """
    Handle Deep Mode queries with iterative API access.

    Claude can make multiple API calls to gather information
    before providing a final answer.
    """
    max_iterations = 10
    api_context = get_api_documentation()

    prompt = f"""{api_context}

User question: {user_message}

Research the knowledge base and provide a comprehensive answer.
Use CALL: curl '<endpoint>' to retrieve information."""

    for iteration in range(max_iterations):
        response = claude.query(prompt, conversation_id)
        conversation_id = response.conversation_id

        # Check for API calls in response
        api_calls = extract_api_calls(response.result)

        if not api_calls:
            # No more API calls - this is the final answer
            return {
                "message": response.result,
                "conversation_id": conversation_id,
                "iterations": iteration + 1
            }

        # Execute API calls and feed results back
        api_results = []
        for call in api_calls:
            result = await execute_api_call(call)
            api_results.append(f"API_RESPONSE ({call}): {result}")

        # Feed results back to Claude
        prompt = "\n".join(api_results) + "\n\nContinue your research or provide your final answer."

    return {
        "message": response.result,
        "conversation_id": conversation_id,
        "iterations": max_iterations,
        "warning": "Max iterations reached"
    }


def extract_api_calls(text: str) -> list[str]:
    """Extract CALL: curl '...' patterns from Claude's response."""
    pattern = r"CALL:\s*curl\s+['\"]([^'\"]+)['\"]"
    return re.findall(pattern, text)


async def execute_api_call(url: str) -> str:
    """Execute an API call and return the result."""
    # Parse URL and route to appropriate handler
    # This is internal - we don't actually use curl
    from app.api import search
    # ... route to appropriate endpoint handler
```

---

## Best Practices

When Claude uses the API effectively:

1. **Start broad, then narrow**: Begin with `/api/search`, then follow threads
2. **Cross-reference speakers**: If someone is mentioned, use `/api/search/speaker`
3. **Understand entities**: Use `/api/entities` to understand systems and relationships
4. **Get full context**: Use `/api/segments/{id}/context` when snippets aren't enough
5. **Check timelines**: Use `/api/topics/{topic}/timeline` for evolution questions
6. **Cite specifically**: Always note the video and timestamp for citations

---

## Security Considerations

- All endpoints are read-only
- API is accessed internally by the backend, not directly by Claude
- Rate limiting can be applied per conversation
- No authentication required for local deployment
