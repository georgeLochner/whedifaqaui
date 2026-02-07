# Project Summary

**Whedifaqaui** is a Video Knowledge Management System that:
- Ingests recorded technical meetings (MKV format)
- Transcribes with speaker diarization (WhisperX)
- Indexes with semantic chunking (embedding-based)
- Enables natural language search via web UI
- All Claude interactions go through a backend wrapper module

**Use Case**: Technical project handover - finding specific information across hours of recorded meetings.

# Documentation

## Structure

```
docs/
├── requirements/     # What to build (user stories, phases, acceptance criteria)
├── design/           # How to build it (technical design, source of truth)
├── implementation/   # Phase-by-phase implementation plans
├── testing/          # Test specifications for verifying each phase
└── reference/        # Detailed specs referenced from design docs
```

## docs/requirements
User stories, UI mockups, and phase definitions. Defines *what* the system must do.

## docs/design
The technical source of truth. **Start with `README.md`** for a high-level overview that ties all design documents together.

The design documentation is organized by system behavior rather than by abstract categories:

| Document | Describes |
|----------|-----------|
| **README.md** | System overview, architecture diagram, and guide to all docs |
| **technology-stack.md** | All tools, libraries, frameworks with pinned versions |
| **data-model.md** | PostgreSQL schema and OpenSearch indices |
| **processing-pipeline.md** | How videos are ingested (upload → transcode → transcribe → chunk → analyze → index) |
| **query-flow.md** | How searches work (Quick mode and Deep mode) |
| **search-api.md** | REST API endpoints exposed for agentic search |
| **claude-integration.md** | The wrapper module pattern for all LLM interactions |
| **deployment.md** | Docker Compose configuration and infrastructure |

## docs/implementation
Phase-specific implementation plans that translate design into actionable tasks.

## docs/testing
Test specifications for verifying delivery of each phase. Each phase has a corresponding test spec (e.g., `phase1-test-specification.md`) defining test cases, acceptance criteria verification, and quality gates.

## docs/reference
Extended specifications referenced from design docs. Keeps design documents focused and readable.

