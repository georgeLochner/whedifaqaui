# Architectural Decision Log

This document captures key architectural and technical decisions made during the planning phase of Whedifaqaui, along with their rationale.

---

## Decision 1: Dual Query Mode Architecture

**Decision**: Implement two query modes - Quick (pre-fetched context) and Deep (agentic with REST API access)

**Options Considered**:
1. Pre-fetched context only (simpler)
2. Agentic search only (more powerful)
3. Both modes with user choice (flexible)

**Choice**: Option 3 - Both modes

**Rationale**:
- Simple questions don't need expensive iterative search
- Complex questions benefit from Claude's ability to follow threads
- Users can choose based on their needs
- Quick mode: ~10-20 seconds, Deep mode: ~30-90 seconds

**Implications**:
- Phase 2 delivers Quick mode
- Phase 4 adds Deep mode with REST API access
- Frontend needs mode toggle or auto-detection

---

## Decision 2: Claude Code CLI as Query Agent

**Decision**: Use Claude Code CLI (`claude -p "prompt"`) instead of building custom LLM orchestration

**Options Considered**:
1. Claude API with custom agent framework
2. LangChain/LlamaIndex orchestration
3. Claude Code CLI with session management

**Choice**: Option 3 - Claude Code CLI

**Rationale**:
- Team already has Claude Code subscriptions (no additional API costs)
- `--session-id` and `--resume` flags provide conversation continuity for free
- Full Claude capabilities without building agent infrastructure
- REST API enables iterative retrieval in Deep mode
- Simpler backend - no need for complex prompt management

**Implications**:
- Backend invokes CLI via subprocess
- Must handle CLI timeouts and errors
- New conversations use `--session-id <uuid>` to set a trackable session ID
- Follow-up queries use `--resume <uuid>` to continue the conversation

---

## Decision 3: Semantic Chunking via Embedding Similarity

**Decision**: Use embedding-based semantic chunking rather than fixed-size or LLM-guided chunking

**Options Considered**:
1. Fixed-size/time-based chunks (simple, fast)
2. Whisper segments as-is (natural but too granular)
3. Semantic chunking via embedding similarity (balanced)
4. LLM-guided chunking (highest quality, expensive)

**Choice**: Option 3 - Semantic chunking with embeddings

**Rationale**:
- Research shows up to 70% improvement over fixed-size chunking
- Whisper provides natural speech boundaries as base units
- Embedding similarity detects topic changes without LLM costs
- Processing is fast: ~1000 segments/second on GPU
- ~90% of LLM-guided quality at ~5% of the cost

**Parameters**:
- Similarity threshold: 0.5
- Target chunk size: 200-500 tokens
- Optional: LLM summaries for concept-level search

**Implications**:
- New pipeline stage (Stage 4: Semantic Chunking)
- Requires embedding model loaded during processing
- Chunks are coherent topics, better for retrieval

---

## Decision 4: OpenSearch for Hybrid Search

**Decision**: Use OpenSearch for search indices rather than PostgreSQL-only (pgvector) or dedicated vector database

**Options Considered**:
1. PostgreSQL + pgvector only (simpler)
2. OpenSearch (hybrid search, scalable)
3. Dedicated vector DB like Pinecone (fastest for vectors)
4. Elasticsearch (similar to OpenSearch)

**Choice**: Option 2 - OpenSearch

**Rationale**:
- Excellent hybrid search (BM25 + vector in single query)
- User comfortable with Docker infrastructure
- Open source, self-hosted (no vendor lock-in)
- Good performance for expected scale (~20+ hours of video)
- Native Reciprocal Rank Fusion (RRF) for combining results

**Implications**:
- Additional Docker container to manage
- Data synced from PostgreSQL (source of truth)
- Can rebuild indices from PostgreSQL if needed

---

## Decision 5: PostgreSQL as Source of Truth

**Decision**: Use PostgreSQL for all structured data, with OpenSearch as derived search index

**Rationale**:
- Clear data ownership - PostgreSQL is authoritative
- OpenSearch indices can be rebuilt from PostgreSQL
- Relational model suits video/transcript/entity relationships
- PostgreSQL handles CRUD operations, OpenSearch handles search
- Simpler consistency model

**Implications**:
- All writes go to PostgreSQL first
- Indexing task syncs to OpenSearch
- If indices corrupt, rebuild from PostgreSQL

---

## Decision 6: Neo4j Deferred to Phase 5

**Decision**: Add Neo4j for knowledge graph visualization in Phase 5, not earlier

**Options Considered**:
1. Include Neo4j from Phase 1
2. Model relationships in PostgreSQL only
3. Add Neo4j when needed (Phase 5)

**Choice**: Option 3 - Add in Phase 5

**Rationale**:
- Entity relationships can be modeled in PostgreSQL initially
- Neo4j adds operational complexity
- Knowledge graph visualization is a Phase 5 feature
- Easier to sync PostgreSQL → Neo4j than maintain both from start
- Can validate relationship model in PostgreSQL first

**Implications**:
- `entity_relationships` table in PostgreSQL from Phase 3
- Neo4j sync added in Phase 5
- Graph queries use Cypher in Phase 5+

---

## Decision 7: BGE Embedding Model (Local)

**Decision**: Use BAAI/bge-base-en-v1.5 for embeddings rather than OpenAI API

**Options Considered**:
1. OpenAI text-embedding-3-small (API, excellent quality)
2. BAAI/bge-base-en-v1.5 (local, very good quality)
3. all-MiniLM-L6-v2 (local, lightweight)
4. nomic-embed-text-v1.5 (local, long context)

**Choice**: Option 2 - BGE base

**Rationale**:
- Free (no API costs for embedding)
- Runs locally on indicated hardware (GPU with 8GB+ VRAM)
- 768 dimensions - good balance of quality and storage
- Very good quality for English text
- Fast: ~1000 embeddings/second on GPU

**Implications**:
- ~2GB VRAM usage for model
- OpenSearch configured for 768 dimensions
- Can switch to OpenAI later if quality needs improvement

---

## Decision 8: faster-whisper for Transcription

**Decision**: Use faster-whisper library with large-v2 model

**Options Considered**:
1. OpenAI Whisper API (cloud, costs money)
2. Original OpenAI Whisper (local, slower)
3. faster-whisper (local, 4x faster)
4. WhisperX (faster-whisper + speaker diarization)

**Choice**: Option 3/4 - faster-whisper (WhisperX for speaker diarization in Phase 3)

**Rationale**:
- Free (runs locally)
- 4x faster than original Whisper
- Excellent accuracy with accented English
- large-v2 model handles diverse speakers well
- Can add WhisperX for speaker diarization later

**Hardware Implications**:
- GPU: 10-20 minutes for 2-hour video
- CPU: 2-4 hours for 2-hour video
- Recommend GPU for acceptable processing time

---

## Decision 9: Desktop-Only UI

**Decision**: Build for desktop browsers only (1200px+), no mobile/tablet responsive design

**Rationale**:
- Primary use case is developers/team at workstations
- Three-panel layout doesn't work well on mobile
- Reduces frontend complexity for POC
- Can add responsive design later if needed

**Implications**:
- Tailwind configured for desktop breakpoints
- No mobile navigation patterns
- Video playback assumes landscape orientation

---

## Decision 10: LLM-Based Entity Extraction (Full Transcript)

**Decision**: Use Claude (via CLI with `--model haiku`) with full timestamped transcript for entity extraction

**Options Considered**:
1. spaCy NER (traditional NLP, fast, limited)
2. Claude per-chunk (LLM, loses context between chunks)
3. Claude full-transcript (LLM, full context, better disambiguation)
4. Local LLM like Llama 3 (free but requires GPU)

**Choice**: Option 3 - Claude with full transcript via CLI

**Rationale**:
- Much better at technical domain entities
- Full transcript context enables natural disambiguation ("John" = same person throughout)
- LLM returns entities WITH timestamps directly (no post-mapping needed)
- Relationships visible in context ("migrate from Auth0 to Cognito")
- Single CLI invocation per video (simpler, fewer failure points)
- Claude's large context easily handles 2-3 hour videos (~20-25K tokens)
- Uses Claude Code CLI with `--model haiku` flag for cost efficiency

**Implementation**:
- All entity extraction goes through the Claude wrapper module (`services/claude.py`)
- Wrapper invokes CLI: `claude -p "prompt" --model haiku`
- No Anthropic API used - consistent with Decision 2

**Approach**:
- Feed timestamped transcript: `[0:00] text... [0:15] text...`
- LLM extracts entities with mention timestamps
- LLM extracts relationships between entities
- For very long videos (4+ hours), fall back to chunked processing

**Cost Estimate**:
- 2-hour video ≈ 20K input tokens + 2K output tokens
- Entity extraction: ~$0.005 per video (using Haiku)
- 20 hours of video: ~$0.05 total

---

## Decision 11: Configurable Chunking Strategy

**Decision**: Support both embedding-based and LLM-based chunking with a configuration toggle

**Options Considered**:
1. Embedding-based only (fast, free, good quality)
2. LLM-based only (better quality, costs money)
3. Configurable with both options + comparison mode

**Choice**: Option 3 - Configurable with comparison mode

**Rationale**:
- Different use cases have different quality/cost tradeoffs
- LLM-based chunking leverages full context understanding
- Embedding-based chunking is faster and free
- "Both" mode enables A/B testing of retrieval quality
- Configuration via Settings UI makes it accessible to non-technical users

**Modes**:

| Mode | Quality | Cost | Speed |
|------|---------|------|-------|
| `embedding` | Good | $0 | Fast |
| `llm` | Better | ~$0.002/video | Medium |
| `both` | Compare | ~$0.002/video | Slower |

**LLM-Based Advantages**:
- Full transcript context for boundary detection
- Natural topic understanding (not just vector similarity)
- Provides chunk summaries automatically
- Better at identifying subtle topic transitions

**Implementation**:
- System Settings UI with radio button selection
- `chunking_method` column in segments table
- Both methods still use BGE for final chunk embeddings (for search)
- Changes apply to newly processed videos

---

## Decision 12: Seven Implementation Phases

**Decision**: Structure implementation into 7 phases with clear dependencies

**Phases**:
1. MVP Core (upload, transcribe, basic search, playback)
2. Conversational AI - Quick Mode
3. Intelligent Analysis (entities, speakers, visual)
4. Agentic Search - Deep Mode (REST API)
5. Knowledge Graph (Neo4j, visualization)
6. Polish & Administration
7. Conversation Persistence

**Rationale**:
- Phase 1 delivers end-to-end testable system quickly
- Each phase builds on previous
- Phases 4 and 5 can run in parallel
- Deep mode (Phase 4) depends on entities from Phase 3
- Clear milestones for progress tracking

---

## Decision 13: REST API for Deep Mode Tool Access

**Decision**: Expose search capabilities via REST API endpoints, with Claude requesting API calls via `curl` commands in its responses

**Rationale**:
- Simple architecture - uses existing FastAPI endpoints
- No additional dependencies (no MCP SDK needed)
- Claude receives API documentation in context prompt
- Backend parses `CALL: curl '<url>'` from Claude's responses
- Executes API calls and feeds results back iteratively
- Full control over what Claude can access

**API Endpoints Exposed**:
- `GET /api/search` - hybrid search
- `GET /api/search/speaker/{name}` - speaker filter
- `GET /api/search/date-range` - temporal filter
- `GET /api/entities/{name}` - entity details
- `GET /api/videos/{id}/transcript` - full transcript
- `GET /api/segments/{id}/context` - expand context
- `GET /api/videos` - browse library
- `GET /api/topics/{name}/timeline` - topic evolution

---

## Hardware Assumptions

Based on discussions, the target hardware is:

**Development**:
- CPU: 4+ cores
- RAM: 16GB minimum
- Storage: 100GB SSD
- GPU: Optional (CPU transcription slower)

**Production**:
- CPU: 8+ cores
- RAM: 32GB
- Storage: 500GB SSD
- GPU: NVIDIA with 8GB+ VRAM (RTX 3080+ or equivalent)

**GPU Impact**:
| Task | With GPU | Without GPU |
|------|----------|-------------|
| Transcription (2hr video) | 10-20 min | 2-4 hours |
| Embedding generation | ~1 sec | ~30 sec |
| Total processing | ~20-35 min | ~2.5-4.5 hours |

---

## Cost Estimates

**One-Time Setup**: $0 (all open source)

**Per-Video Processing** (2-hour video):
- Transcription: $0 (local)
- Embeddings: $0 (local)
- Entity extraction (Haiku): ~$0.01
- Summary generation (optional): ~$0.01

**Per-Query**:
- Quick mode: $0 (Claude Code subscription)
- Deep mode: $0 (Claude Code subscription)

**Infrastructure**:
- Self-hosted: electricity + hardware
- No cloud API costs for core functionality

---

## Open Questions for Future Sessions

1. **Authentication**: Currently deferred - when/if to add user auth?
2. **Multi-tenancy**: Single team for now, but future expansion?
3. **Backup strategy**: Automated backups for PostgreSQL and videos?
4. **Monitoring**: What metrics to track in production?
5. **Video format expansion**: Support formats beyond MKV?
