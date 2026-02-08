# Deployment

## Overview

Whedifaqaui is deployed using Docker Compose, which orchestrates all required services in containers.

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           Docker Compose                                     │
│                                                                              │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  frontend   │  │   backend   │  │   worker    │  │      worker-gpu     │ │
│  │  (React)    │  │  (FastAPI)  │  │  (Celery)   │  │  (Celery + CUDA)    │ │
│  │  Port 3000  │  │  Port 8000  │  │             │  │  (if GPU available) │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│         │                │                │                    │            │
│         │                │                │                    │            │
│  ┌──────┴────────────────┴────────────────┴────────────────────┴──────────┐ │
│  │                           Internal Network                              │ │
│  └────────────────────────────────────────────────────────────────────────┘ │
│         │                │                │                    │            │
│         │                │                │                    │            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐ │
│  │  postgres   │  │  opensearch │  │    redis    │  │    neo4j (Phase 5)  │ │
│  │  Port 5432  │  │  Port 9200  │  │  Port 6379  │  │  Ports 7474, 7687   │ │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────────────┘ │
│                                                                              │
│  ┌──────────────────────────────────────────────────────────────────────┐   │
│  │                          Volumes                                      │   │
│  │  postgres_data | opensearch_data | redis_data | video_data | models  │   │
│  └──────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Docker Compose Configuration

**⚠️ Image Versions Are Frozen** - Do not change versions shown below. See `technology-stack.md` for version freeze policy.

```yaml
# docker-compose.yml

version: '3.8'

services:
  # ============================================
  # DATABASE SERVICES
  # ============================================

  postgres:
    image: postgres:16.1-alpine
    environment:
      POSTGRES_USER: whedifaqaui
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-devpassword}
      POSTGRES_DB: whedifaqaui
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sql:/docker-entrypoint-initdb.d/init.sql
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U whedifaqaui"]
      interval: 10s
      timeout: 5s
      retries: 5

  opensearch:
    image: opensearchproject/opensearch:2.11.1
    environment:
      - discovery.type=single-node
      - plugins.security.disabled=true  # Disable for dev simplicity
      - OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m
      - bootstrap.memory_lock=true
    ulimits:
      memlock:
        soft: -1
        hard: -1
      nofile:
        soft: 65536
        hard: 65536
    volumes:
      - opensearch_data:/usr/share/opensearch/data
    ports:
      - "9200:9200"
    healthcheck:
      test: ["CMD-SHELL", "curl -s http://localhost:9200 || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 5

  redis:
    image: redis:7.2.4-alpine
    volumes:
      - redis_data:/data
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5

  # ============================================
  # APPLICATION SERVICES
  # ============================================

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://whedifaqaui:${POSTGRES_PASSWORD:-devpassword}@postgres:5432/whedifaqaui
      - OPENSEARCH_URL=http://opensearch:9200
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - VIDEO_STORAGE_PATH=/data/videos
      - TRANSCRIPT_STORAGE_PATH=/data/transcripts
    volumes:
      - video_data:/data/videos
      - transcript_data:/data/transcripts
      - model_cache:/root/.cache  # Cache for ML models
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      opensearch:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://whedifaqaui:${POSTGRES_PASSWORD:-devpassword}@postgres:5432/whedifaqaui
      - OPENSEARCH_URL=http://opensearch:9200
      - REDIS_URL=redis://redis:6379/0
      - CELERY_BROKER_URL=redis://redis:6379/0
      - VIDEO_STORAGE_PATH=/data/videos
      - TRANSCRIPT_STORAGE_PATH=/data/transcripts
      - WHISPER_MODEL=medium  # Use medium for CPU
      - WHISPER_DEVICE=cpu
    volumes:
      - video_data:/data/videos
      - transcript_data:/data/transcripts
      - model_cache:/root/.cache
    depends_on:
      postgres:
        condition: service_healthy
      opensearch:
        condition: service_healthy
      redis:
        condition: service_healthy
    command: celery -A app.celery_app worker --loglevel=info --concurrency=2

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - backend

  # ============================================
  # OPTIONAL: GPU WORKER (uncomment if GPU available)
  # ============================================

  # worker-gpu:
  #   build:
  #     context: ./backend
  #     dockerfile: Dockerfile.gpu
  #   environment:
  #     - DATABASE_URL=postgresql://whedifaqaui:${POSTGRES_PASSWORD:-devpassword}@postgres:5432/whedifaqaui
  #     - OPENSEARCH_URL=http://opensearch:9200
  #     - REDIS_URL=redis://redis:6379/0
  #     - CELERY_BROKER_URL=redis://redis:6379/0
  #     - VIDEO_STORAGE_PATH=/data/videos
  #     - TRANSCRIPT_STORAGE_PATH=/data/transcripts
  #     - WHISPER_MODEL=large-v2
  #     - WHISPER_DEVICE=cuda
  #   volumes:
  #     - video_data:/data/videos
  #     - transcript_data:/data/transcripts
  #     - model_cache:/root/.cache
  #   deploy:
  #     resources:
  #       reservations:
  #         devices:
  #           - driver: nvidia
  #             count: 1
  #             capabilities: [gpu]
  #   command: celery -A app.celery_app worker --loglevel=info --concurrency=1 -Q transcription

  # ============================================
  # PHASE 5: NEO4J (uncomment when needed)
  # ============================================

  # neo4j:
  #   image: neo4j:5.15.0-community
  #   environment:
  #     - NEO4J_AUTH=neo4j/${NEO4J_PASSWORD:-devpassword}
  #     - NEO4J_PLUGINS=["apoc"]
  #   volumes:
  #     - neo4j_data:/data
  #   ports:
  #     - "7474:7474"  # Web UI
  #     - "7687:7687"  # Bolt protocol

volumes:
  postgres_data:
  opensearch_data:
  redis_data:
  video_data:
  transcript_data:
  model_cache:
  # neo4j_data:  # Uncomment for Phase 5
```

## Backend Dockerfile

```dockerfile
# backend/Dockerfile

FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    libsndfile1 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download embedding model on build (optional, speeds up startup)
RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-base-en-v1.5')"

# Copy application code
COPY . .

# Create data directories
RUN mkdir -p /data/videos/original /data/videos/processed /data/videos/audio /data/videos/thumbnails /data/transcripts

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## GPU Worker Dockerfile

```dockerfile
# backend/Dockerfile.gpu

FROM nvidia/cuda:12.1-runtime-ubuntu22.04

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    ffmpeg \
    libsndfile1 \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Install CUDA-enabled faster-whisper
RUN pip3 install faster-whisper

# Pre-download Whisper model
RUN python3 -c "from faster_whisper import WhisperModel; WhisperModel('large-v2', device='cuda', compute_type='float16')"

COPY . .

RUN mkdir -p /data/videos/original /data/videos/processed /data/videos/audio /data/videos/thumbnails /data/transcripts

CMD ["celery", "-A", "app.celery_app", "worker", "--loglevel=info", "--concurrency=1", "-Q", "transcription"]
```

## Frontend Dockerfile

```dockerfile
# frontend/Dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]
```

## Environment Variables

Create a `.env` file in the project root:

```bash
# .env

# Database
POSTGRES_PASSWORD=your_secure_password

# Neo4j (Phase 4)
NEO4J_PASSWORD=your_secure_password

# OpenSearch (if security enabled)
OPENSEARCH_USER=admin
OPENSEARCH_PASSWORD=admin

# Application
SECRET_KEY=your_secret_key_for_sessions

# Whisper (uncomment one)
# WHISPER_MODEL=large-v2  # GPU
WHISPER_MODEL=medium      # CPU

# Note: No Anthropic API key needed - all Claude interactions use Claude Code CLI
```

## Startup Commands

### Development

**For development work (recommended)**, use development mode with volume mounts and hot reload:

```bash
# Start all services with development overrides
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# View logs
docker compose logs -f

# View specific service logs
docker compose logs -f backend
docker compose logs -f worker

# Changes to code reflect immediately (no rebuild needed)
# Just restart service if needed:
docker compose restart backend

# Stop all services
docker compose down
```

#### docker-compose.dev.yml

Development overrides add volume mounts (so code edits on the host reflect immediately in containers) and hot-reload commands:

```yaml
# docker-compose.dev.yml
services:
  backend:
    volumes:
      - ./backend:/app
      - video_data:/data/videos
      - transcript_data:/data/transcripts
      - model_cache:/root/.cache
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  worker:
    volumes:
      - ./backend:/app
      - video_data:/data/videos
      - transcript_data:/data/transcripts
      - model_cache:/root/.cache

  frontend:
    volumes:
      - ./frontend:/app
      - /app/node_modules
    command: npm run dev -- --host 0.0.0.0
```

**For detailed development workflow**, see [Development Documentation](../development/docker-workflow.md).

### Production

```bash
# Build images
docker compose -f docker-compose.yml -f docker-compose.prod.yml build

# Start with production overrides
docker compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Scale workers
docker compose up -d --scale worker=3
```

## Initial Setup

After starting services for the first time:

```bash
# 1. Run database migrations
docker compose exec backend alembic upgrade head

# 2. Create OpenSearch indices
docker compose exec backend python scripts/create_indices.py

# 3. Verify services are healthy
docker compose ps
```

## Data Persistence

| Volume | Contents | Backup Priority |
|--------|----------|-----------------|
| `postgres_data` | All metadata, entities, relationships | Critical |
| `opensearch_data` | Search indices (can be rebuilt) | Low |
| `redis_data` | Task queue (ephemeral) | None |
| `video_data` | Original and processed videos | Critical |
| `transcript_data` | Raw transcript files | Medium |
| `model_cache` | Downloaded ML models | None (re-downloads) |

## Backup Strategy

```bash
# Backup PostgreSQL
docker compose exec postgres pg_dump -U whedifaqaui whedifaqaui > backup.sql

# Backup videos (rsync to backup location)
rsync -av /var/lib/docker/volumes/whedifaqaui_video_data/_data/ /backup/videos/

# Restore PostgreSQL
cat backup.sql | docker compose exec -T postgres psql -U whedifaqaui whedifaqaui
```

## Resource Requirements

### Minimum (CPU-only)

| Resource | Minimum |
|----------|---------|
| CPU | 4 cores |
| RAM | 16 GB |
| Storage | 100 GB SSD |

### Recommended (with GPU)

| Resource | Recommended |
|----------|-------------|
| CPU | 8 cores |
| RAM | 32 GB |
| Storage | 500 GB SSD |
| GPU | NVIDIA with 8GB+ VRAM |

## Health Checks

```bash
# Check all services
curl http://localhost:8000/health
curl http://localhost:9200/_cluster/health
docker compose exec redis redis-cli ping

# Check Celery workers
docker compose exec backend celery -A app.celery_app inspect active
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| OpenSearch won't start | Increase `vm.max_map_count`: `sudo sysctl -w vm.max_map_count=262144` |
| Out of memory | Reduce OpenSearch heap: `OPENSEARCH_JAVA_OPTS=-Xms256m -Xmx256m` |
| Slow transcription | Use GPU worker or switch to `medium` model |
| Videos not playing | Check FFmpeg transcoding logs, verify MP4 output |
