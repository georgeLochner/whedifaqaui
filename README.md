# Whedifaqaui

Video Knowledge Management System - Ingest technical meeting recordings, transcribe with speaker diarization, and search using natural language.

## Prerequisites

- Docker and Docker Compose
- Git

## Quick Start

1. **Clone and setup environment**
   ```bash
   git clone <repository-url>
   cd whedifaqaui
   cp .env.example .env
   ```

2. **Create data directories**
   ```bash
   mkdir -p data/{videos/{original,processed,audio,thumbnails,screenshots},transcripts,temp,models}
   ```

3. **Start all services**
   ```bash
   docker compose up -d
   ```

4. **Wait for services to be healthy** (may take a few minutes on first run)
   ```bash
   docker compose ps
   ```

5. **Verify environment**
   ```bash
   ./scripts/verify-environment.sh
   ```

## Services

| Service | URL | Description |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | React web interface |
| Backend API | http://localhost:8000 | FastAPI REST API |
| API Docs | http://localhost:8000/docs | Swagger UI |
| PostgreSQL | localhost:5432 | Primary database |
| OpenSearch | http://localhost:9200 | Search engine |
| Redis | localhost:6379 | Celery broker |

## Development

### Common Commands

```bash
# Start all services
make up

# View logs
make logs

# Stop all services
make down

# Open shell in backend container
make shell-backend

# Run tests
make test

# Run linters
make lint

# Full cleanup (removes volumes)
make clean
```

### Project Structure

```
whedifaqaui/
├── backend/           # FastAPI application
│   ├── app/
│   │   ├── api/       # Route handlers
│   │   ├── core/      # Config, database, dependencies
│   │   ├── models/    # SQLAlchemy models
│   │   ├── schemas/   # Pydantic schemas
│   │   ├── services/  # Business logic
│   │   └── tasks/     # Celery tasks
│   ├── alembic/       # Database migrations
│   └── tests/
├── frontend/          # React application
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── services/  # API client
│       └── types/
├── docker/            # Dockerfiles
├── scripts/           # Utility scripts
├── data/              # Runtime data (git-ignored)
└── docs/              # Documentation
```

### Environment Variables

See `.env.example` for all available configuration options.

## Architecture

- **Frontend**: React 18 + Vite + Tailwind CSS
- **Backend**: FastAPI + SQLAlchemy + Celery
- **Database**: PostgreSQL 16 (source of truth)
- **Search**: OpenSearch 2.11 (semantic search)
- **Transcription**: WhisperX with speaker diarization
- **LLM**: Claude CLI for content analysis

## License

Proprietary
