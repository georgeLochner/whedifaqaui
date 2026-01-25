# Query Flow

## Overview

Whedifaqaui supports two query modes:

| Mode | Description | Latency | Best For |
|------|-------------|---------|----------|
| **Quick Answer** (Phase 2) | Pre-fetched context passed to Claude | ~10-20 seconds | Simple, direct questions |
| **Deep Research** (Phase 4) | Claude requests API calls iteratively | ~30-90 seconds | Complex, multi-faceted questions |

Users can choose which mode to use, or the system can auto-select based on query complexity.

---

## Mode 1: Quick Answer (Pre-fetched Context)

When a user asks a question through the web interface, the query flows through several components before returning a synthesized answer with citations.

## Query Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER                                            │
│                                                                              │
│  "What did John say about migrating from Auth0 to Cognito?"                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ POST /api/query
                                    │ { question, session_id? }
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FASTAPI BACKEND                                      │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  1. SESSION MANAGEMENT                                                 │  │
│  │     - If no session_id, generate new UUID                             │  │
│  │     - Track conversation history per session                          │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
│                                    ▼                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  2. QUERY EMBEDDING                                                    │  │
│  │     - Generate embedding for user question using BGE model            │  │
│  │     - embedding = model.encode(question)                              │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
│                                    ▼                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  3. HYBRID SEARCH (OpenSearch)                                         │  │
│  │                                                                        │  │
│  │     ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                 │  │
│  │     │   Vector    │  │   Keyword   │  │   Filter    │                 │  │
│  │     │   Search    │  │   Search    │  │   (Entity)  │                 │  │
│  │     │   (kNN)     │  │   (BM25)    │  │             │                 │  │
│  │     └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                 │  │
│  │            │                │                │                         │  │
│  │            └────────────────┼────────────────┘                         │  │
│  │                             ▼                                          │  │
│  │                   ┌─────────────────┐                                  │  │
│  │                   │  Reciprocal     │                                  │  │
│  │                   │  Rank Fusion    │                                  │  │
│  │                   └────────┬────────┘                                  │  │
│  │                            │                                           │  │
│  │                            ▼                                           │  │
│  │                   Top 10-20 segments                                   │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
│                                    ▼                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  4. CONTEXT PREPARATION                                                │  │
│  │                                                                        │  │
│  │     For each retrieved segment:                                       │  │
│  │     - Load full segment text                                          │  │
│  │     - Include video title, timestamp                                  │  │
│  │     - Include speaker if known                                        │  │
│  │     - Include surrounding context if needed                           │  │
│  │                                                                        │  │
│  │     Format as structured context block                                │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
│                                    ▼                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  5. CLAUDE CODE CLI INVOCATION                                         │  │
│  │                                                                        │  │
│  │     New:    claude -p "$PROMPT" --session-id $SESSION_ID              │  │
│  │     Resume: claude -p "$PROMPT" --resume $SESSION_ID                  │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
│                                    ▼                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  6. RESPONSE PARSING                                                   │  │
│  │                                                                        │  │
│  │     - Extract answer text                                             │  │
│  │     - Parse citations (video + timestamp references)                  │  │
│  │     - Build result objects for frontend                               │  │
│  │                                                                        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ Response
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                              FRONTEND                                        │
│                                                                              │
│  {                                                                          │
│    "answer": "John discussed the Auth0 to Cognito migration in two...",    │
│    "session_id": "abc-123",                                                 │
│    "sources": [                                                             │
│      {                                                                      │
│        "video_id": "vid-456",                                               │
│        "video_title": "Auth System Deep Dive",                              │
│        "timestamp": 734,                                                    │
│        "timestamp_formatted": "12:14",                                      │
│        "excerpt": "So we decided to migrate from Auth0 because...",         │
│        "speaker": "John"                                                    │
│      },                                                                     │
│      ...                                                                    │
│    ]                                                                        │
│  }                                                                          │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Implementation Details

### Step 3: Hybrid Search Query

```python
def hybrid_search(question: str, embedding: list, limit: int = 20) -> list:
    """
    Perform hybrid search combining vector similarity and keyword matching.
    """

    query = {
        "size": limit,
        "query": {
            "hybrid": {
                "queries": [
                    # Vector search (semantic similarity)
                    {
                        "knn": {
                            "embedding": {
                                "vector": embedding,
                                "k": limit
                            }
                        }
                    },
                    # Keyword search (BM25)
                    {
                        "match": {
                            "text": {
                                "query": question,
                                "fuzziness": "AUTO"
                            }
                        }
                    }
                ]
            }
        },
        # Combine results with RRF
        "search_pipeline": {
            "phase_results_processors": [
                {
                    "normalization-processor": {
                        "normalization": {
                            "technique": "min_max"
                        },
                        "combination": {
                            "technique": "rrf",
                            "parameters": {
                                "rank_constant": 60
                            }
                        }
                    }
                }
            ]
        }
    }

    response = opensearch_client.search(
        index="segments_index",
        body=query
    )

    return response['hits']['hits']
```

### Step 4: Context Preparation

```python
def prepare_context(segments: list, max_tokens: int = 8000) -> str:
    """
    Format retrieved segments as context for Claude.
    """
    context_parts = []

    for i, segment in enumerate(segments, 1):
        source = segment['_source']
        timestamp = format_timestamp(source['start_time'])

        context_parts.append(f"""
--- Source {i} ---
Video: {source['video_title']}
Timestamp: {timestamp}
Speaker: {source.get('speaker', 'Unknown')}
Date: {source['recording_date']}

{source['text']}
""")

    context = "\n".join(context_parts)

    # Truncate if too long (rough token estimate)
    if len(context) > max_tokens * 4:
        context = context[:max_tokens * 4] + "\n\n[Context truncated...]"

    return context
```

### Step 5: Claude CLI Invocation

```python
import subprocess
import shlex

def query_claude(question: str, context: str, session_id: str) -> str:
    """
    Invoke Claude Code CLI with the prepared context.
    """

    prompt = f"""You are a knowledge assistant for a video archive of technical meetings.
Based on the following transcript excerpts, answer the user's question.

IMPORTANT INSTRUCTIONS:
1. Only use information from the provided context
2. Always cite your sources using the format: [Video Title @ timestamp]
3. If the context doesn't contain enough information, say so
4. Be concise but thorough

CONTEXT:
{context}

USER QUESTION:
{question}

Provide a helpful answer with citations:"""

    # Escape the prompt for shell
    # Build command based on whether this is a new or resumed conversation
    cmd = ["claude", "-p", prompt, "--output-format", "text"]
    if is_new_session:
        cmd.extend(["--session-id", session_id])  # Set session ID for new conversation
    else:
        cmd.extend(["--resume", session_id])  # Resume existing conversation

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=120  # 2 minute timeout
    )

    if result.returncode != 0:
        raise Exception(f"Claude CLI error: {result.stderr}")

    return result.stdout
```

### Step 6: Response Parsing

```python
import re

def parse_response(answer: str, segments: list) -> dict:
    """
    Parse Claude's response and extract citations.
    """

    # Extract citations like [Video Title @ 12:34]
    citation_pattern = r'\[([^\]]+)\s*@\s*(\d{1,2}:\d{2}(?::\d{2})?)\]'
    citations = re.findall(citation_pattern, answer)

    # Build source objects
    sources = []
    for segment in segments:
        source = segment['_source']
        sources.append({
            'video_id': source['video_id'],
            'video_title': source['video_title'],
            'timestamp': source['start_time'],
            'timestamp_formatted': format_timestamp(source['start_time']),
            'excerpt': source['text'][:200] + '...',
            'speaker': source.get('speaker')
        })

    return {
        'answer': answer,
        'sources': sources,
        'citations': [
            {'video': c[0], 'timestamp': c[1]}
            for c in citations
        ]
    }
```

## API Endpoint

```python
# api/routes/query.py

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
import uuid

router = APIRouter()

class QueryRequest(BaseModel):
    question: str
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    answer: str
    session_id: str
    sources: list
    citations: list

@router.post("/query", response_model=QueryResponse)
async def query_knowledge_base(request: QueryRequest):
    # 1. Session management
    session_id = request.session_id or str(uuid.uuid4())

    # 2. Generate embedding
    embedding = embedding_model.encode(request.question).tolist()

    # 3. Hybrid search
    segments = hybrid_search(request.question, embedding)

    if not segments:
        return QueryResponse(
            answer="I couldn't find any relevant information in the video archive.",
            session_id=session_id,
            sources=[],
            citations=[]
        )

    # 4. Prepare context
    context = prepare_context(segments)

    # 5. Query Claude
    try:
        answer = query_claude(request.question, context, session_id)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

    # 6. Parse response
    result = parse_response(answer, segments)
    result['session_id'] = session_id

    return QueryResponse(**result)
```

## Conversation Continuity

Claude Code CLI's `--session-id` and `--resume` parameters enable multi-turn conversations:
- `--session-id <uuid>`: Set a specific session ID when starting a new conversation
- `--resume <uuid>`: Resume an existing conversation by its session ID

```
Turn 1:
  User: "What did John say about Auth0?"
  Claude: "John discussed Auth0 in two videos..."

Turn 2 (same session_id):
  User: "What were the specific problems he mentioned?"
  Claude: "Building on the previous discussion, John mentioned three specific issues..."
```

The session ID should be:
- Generated on first query
- Stored in frontend state
- Passed with subsequent queries
- Optionally persisted (Phase 7)

## Performance Characteristics

| Step | Typical Latency |
|------|-----------------|
| Query Embedding | 50-100ms |
| Hybrid Search | 100-300ms |
| Context Preparation | 50-100ms |
| Claude CLI | 5-20 seconds |
| Response Parsing | 10-50ms |
| **Total** | **~6-21 seconds** |

The Claude CLI invocation dominates the latency. This is acceptable for a knowledge query system where users expect thoughtful responses.

## Error Handling

| Error | Handling |
|-------|----------|
| No search results | Return helpful "no results" message |
| Claude CLI timeout | Return error, suggest retry |
| Claude CLI failure | Return error with details |
| Invalid session | Create new session transparently |

---

## Mode 2: Deep Research (Agentic Search) - Phase 4

In Deep Research mode, Claude is given documentation for available REST API endpoints and can request data iteratively. The backend parses Claude's API call requests, executes them, and feeds results back until Claude has enough information to answer.

### Agentic Flow Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              USER                                            │
│                                                                              │
│  "Why did we switch from Auth0 to Cognito and what problems did we face?"   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    │ POST /api/query { question, mode: "deep" }
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FASTAPI BACKEND                                      │
│                                                                              │
│  1. Send question + API documentation to Claude                             │
│  2. Parse Claude's response for CALL: curl requests                         │
│  3. Execute API calls, feed results back to Claude                          │
│  4. Loop until Claude provides final answer                                 │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                    CLAUDE WITH API ACCESS                                    │
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Iteration 1:                                                          │  │
│  │  "I need to find info about Auth0 to Cognito migration..."            │  │
│  │                                                                        │  │
│  │  CALL: curl 'http://localhost:8000/api/search?query=Auth0+Cognito'    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
│                  Backend executes, feeds back results                       │
│                                    ▼                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Iteration 2:                                                          │  │
│  │  "John seems to have discussed this. Let me find more from him..."    │  │
│  │                                                                        │  │
│  │  CALL: curl 'http://localhost:8000/api/search/speaker/John?query=auth'│  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
│                  Backend executes, feeds back results                       │
│                                    ▼                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Iteration 3:                                                          │  │
│  │  "I want to understand the Cognito entity and relationships..."       │  │
│  │                                                                        │  │
│  │  CALL: curl 'http://localhost:8000/api/entities/cognito'              │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                    │                                         │
│                  Backend executes, feeds back results                       │
│                                    ▼                                         │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  Final Iteration:                                                      │  │
│  │  "I now have comprehensive context. Synthesizing answer..."           │  │
│  │                                                                        │  │
│  │  [No CALL: - provides final answer with citations]                    │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                           RESPONSE                                           │
│                                                                              │
│  Comprehensive answer covering:                                             │
│  - The decision rationale (from migration discussions)                      │
│  - John's specific perspective (from speaker-filtered search)              │
│  - Problems encountered (from issues search)                                │
│  - Timeline and context (from entity info)                                  │
│                                                                              │
│  All with precise citations: [Video Title @ timestamp]                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### API Endpoints Available to Claude

| Endpoint | Purpose | When to Use |
|----------|---------|-------------|
| `GET /api/search` | Semantic + keyword search | Starting point for any topic |
| `GET /api/search/speaker/{name}` | Filter by who said it | "What did X say about Y?" |
| `GET /api/search/date-range` | Filter by recording date | "What was discussed in Q4?" |
| `GET /api/entities/{name}` | Entity details + relationships | Understanding a system/person/project |
| `GET /api/videos/{id}/transcript` | Full transcript of one video | Deep dive into specific meeting |
| `GET /api/segments/{id}/context` | Expand context around a segment | Need more surrounding context |
| `GET /api/videos` | List available videos | Orientation, discovery |
| `GET /api/topics/{name}/timeline` | Chronological view of topic | Understanding evolution |

See [Search API](search-api.md) for full endpoint specifications.

### Backend Implementation (Deep Research)

```python
# api/routes/query.py

import re
from app.services.claude import claude

API_DOCUMENTATION = """
You have access to a video knowledge base API. To retrieve information,
include API calls in your response using this format:

CALL: curl '<endpoint>'

Available endpoints:
- GET /api/search?query=<text>&limit=<n>&speaker=<name>
- GET /api/search/speaker/<name>?query=<text>
- GET /api/search/date-range?start=YYYY-MM-DD&end=YYYY-MM-DD&query=<text>
- GET /api/entities/<name>
- GET /api/videos/<id>/transcript
- GET /api/segments/<id>/context?before=<n>&after=<n>
- GET /api/videos?limit=<n>
- GET /api/topics/<name>/timeline

After each CALL:, I will provide the API response. Continue researching
until you have enough information, then provide your final answer.
Always cite sources using [Video Title @ MM:SS] format.
"""


@router.post("/query/deep", response_model=QueryResponse)
async def deep_research(request: QueryRequest):
    """
    Handle Deep Research mode with iterative API access.
    """
    session_id = request.session_id or str(uuid.uuid4())
    max_iterations = 10

    prompt = f"""{API_DOCUMENTATION}

USER QUESTION:
{request.question}

Research this thoroughly and provide a comprehensive answer."""

    for iteration in range(max_iterations):
        response = claude.query(prompt, session_id)
        session_id = response.conversation_id

        # Check for API calls in response
        api_calls = extract_api_calls(response.result)

        if not api_calls:
            # No more API calls - this is the final answer
            return QueryResponse(
                answer=response.result,
                session_id=session_id,
                sources=extract_sources_from_answer(response.result),
                citations=extract_citations(response.result),
                mode="deep",
                iterations=iteration + 1
            )

        # Execute API calls and feed results back
        api_results = []
        for call in api_calls:
            result = await execute_api_call(call)
            api_results.append(f"API_RESPONSE ({call}):\n{result}")

        # Feed results back to Claude
        prompt = "\n\n".join(api_results) + "\n\nContinue your research or provide your final answer."

    # Max iterations reached
    return QueryResponse(
        answer=response.result,
        session_id=session_id,
        mode="deep",
        warning="Max iterations reached"
    )


def extract_api_calls(text: str) -> list[str]:
    """Extract CALL: curl '...' patterns from Claude's response."""
    pattern = r"CALL:\s*curl\s+['\"]([^'\"]+)['\"]"
    return re.findall(pattern, text)


async def execute_api_call(url: str) -> str:
    """Execute an API call internally and return the result."""
    # Parse URL and route to appropriate handler
    # This is internal - we don't actually use curl
    # Route to the appropriate FastAPI endpoint handler
    ...
```

### Performance Characteristics (Deep Research)

| Metric | Typical Value |
|--------|---------------|
| Tool calls | 3-8 per query |
| Time per tool call | 1-3 seconds |
| Claude reasoning | 10-30 seconds |
| **Total latency** | **30-90 seconds** |
| Token usage | 2-5x Quick Answer mode |

### When to Use Each Mode

| Query Type | Recommended Mode |
|------------|-----------------|
| "When was X discussed?" | Quick Answer |
| "What did John say about Y?" | Quick Answer |
| "Why did we do X and what were the consequences?" | Deep Research |
| "Explain the evolution of our auth system" | Deep Research |
| "Compare what different people said about X" | Deep Research |
| "What are all the systems related to Y?" | Deep Research |

### Frontend Integration

```typescript
// Frontend: Let user choose mode or auto-detect

interface QueryOptions {
  question: string;
  mode: 'quick' | 'deep' | 'auto';
  session_id?: string;
}

async function query(options: QueryOptions) {
  const mode = options.mode === 'auto'
    ? detectComplexity(options.question)
    : options.mode;

  const endpoint = mode === 'deep' ? '/api/query/deep' : '/api/query';

  // Show appropriate loading state
  if (mode === 'deep') {
    showResearchProgress("Claude is researching your question...");
  }

  const response = await fetch(endpoint, {
    method: 'POST',
    body: JSON.stringify(options)
  });

  return response.json();
}

function detectComplexity(question: string): 'quick' | 'deep' {
  // Heuristics for query complexity
  const complexIndicators = [
    /why did/i,
    /what were the (problems|issues|challenges)/i,
    /compare/i,
    /evolution/i,
    /history of/i,
    /everything about/i,
    /relationship between/i
  ];

  return complexIndicators.some(r => r.test(question)) ? 'deep' : 'quick';
}
