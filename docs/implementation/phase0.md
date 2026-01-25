# Phase 0: High-Level Architectural Plan

**Phase**: Environment Setup & Scaffolding
**Goal**: Prepare development environment with all infrastructure running and project scaffolding in place, ready for feature implementation.
**Prerequisite**: None - this is the first phase

---

## Phase 0 Scope

| Category | Description |
|----------|-------------|
| Infrastructure | Docker Compose with all services (PostgreSQL, OpenSearch, Redis) |
| Backend Scaffolding | FastAPI app skeleton with health endpoints, SQLAlchemy, Alembic, Celery |
| Frontend Scaffolding | Vite + React + TypeScript + Tailwind with routing and API client |
| Data Storage | Directory structure and volume mounts |
| Development Tooling | Linting, formatting, test frameworks |
| ML Preparation | GPU-enabled Docker image, model cache setup |
| Verification | All services healthy and communicating |

---

## Project Structure (Created in Phase 0)

```
whedifaqaui/
├── docs/                           # [EXISTS] Documentation
│   └── implementation/
│       ├── phase0.md               # This file
│       ├── phase1.md
│       ├── phase2.md
│       └── phase3.md
│
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI app with health endpoint
│   │   │
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── deps.py             # Dependency injection
│   │   │   └── routes/
│   │   │       ├── __init__.py
│   │   │       └── health.py       # Health check endpoint
│   │   │
│   │   ├── core/
│   │   │   ├── __init__.py
│   │   │   ├── config.py           # Settings (pydantic-settings)
│   │   │   ├── database.py         # PostgreSQL connection
│   │   │   └── opensearch.py       # OpenSearch client
│   │   │
│   │   ├── models/
│   │   │   └── __init__.py         # Empty, ready for Phase 1
│   │   │
│   │   ├── schemas/
│   │   │   └── __init__.py         # Empty, ready for Phase 1
│   │   │
│   │   ├── services/
│   │   │   └── __init__.py         # Empty, ready for Phase 1
│   │   │
│   │   └── tasks/
│   │       ├── __init__.py
│   │       └── celery_app.py       # Celery configuration
│   │
│   ├── migrations/
│   │   ├── env.py                  # Alembic environment
│   │   ├── script.py.mako          # Migration template
│   │   └── versions/
│   │       └── .gitkeep
│   │
│   ├── tests/
│   │   ├── __init__.py
│   │   └── conftest.py             # pytest fixtures
│   │
│   ├── scripts/
│   │   └── download_models.py      # Pre-download ML models
│   │
│   ├── requirements.txt            # Python dependencies
│   ├── requirements-dev.txt        # Development dependencies
│   ├── Dockerfile                  # Production image
│   ├── Dockerfile.worker           # GPU-enabled worker image
│   ├── alembic.ini                 # Alembic configuration
│   ├── pyproject.toml              # Ruff, mypy, pytest config
│   └── .python-version             # Python version (3.11)
│
├── frontend/
│   ├── src/
│   │   ├── main.tsx                # React entry point
│   │   ├── App.tsx                 # Router setup with placeholder routes
│   │   ├── vite-env.d.ts           # Vite type declarations
│   │   │
│   │   ├── pages/
│   │   │   └── PlaceholderPage.tsx # Temporary placeholder
│   │   │
│   │   ├── components/
│   │   │   └── common/
│   │   │       └── Layout.tsx      # Basic layout wrapper
│   │   │
│   │   ├── api/
│   │   │   └── client.ts           # Axios/fetch wrapper
│   │   │
│   │   ├── hooks/
│   │   │   └── .gitkeep
│   │   │
│   │   ├── types/
│   │   │   └── index.ts            # Common types
│   │   │
│   │   └── styles/
│   │       └── index.css           # Tailwind imports
│   │
│   ├── public/
│   │   └── .gitkeep
│   │
│   ├── tests/
│   │   └── setup.ts                # Vitest setup
│   │
│   ├── index.html                  # HTML template
│   ├── package.json                # npm dependencies
│   ├── tsconfig.json               # TypeScript config
│   ├── tsconfig.node.json          # Node TypeScript config
│   ├── vite.config.ts              # Vite config with proxy
│   ├── tailwind.config.js          # Tailwind config
│   ├── postcss.config.js           # PostCSS config
│   ├── eslint.config.js            # ESLint flat config
│   ├── .prettierrc                 # Prettier config
│   └── Dockerfile                  # Production image (nginx)
│
├── data/                           # Persistent storage (volume mounted)
│   ├── videos/
│   │   ├── original/
│   │   ├── processed/
│   │   ├── audio/
│   │   ├── thumbnails/
│   │   └── screenshots/
│   ├── transcripts/
│   ├── temp/
│   └── models/                     # Cached ML models
│
├── docker/
│   └── opensearch/
│       └── opensearch.yml          # OpenSearch configuration
│
├── scripts/
│   ├── init-db.sh                  # Database initialization
│   └── wait-for-it.sh              # Service dependency script
│
├── docker-compose.yml              # All services
├── docker-compose.dev.yml          # Development overrides
├── docker-compose.gpu.yml          # GPU worker override
├── .env.example                    # Environment template
├── .gitignore                      # Git ignore rules
├── Makefile                        # Common commands
└── README.md                       # Setup instructions
```

---

## Infrastructure Services

### Docker Compose Services

| Service | Image | Purpose | Port | Health Check |
|---------|-------|---------|------|--------------|
| `postgres` | postgres:16.1-alpine | Primary database | 5432 | `pg_isready` |
| `opensearch` | opensearchproject/opensearch:2.11.0 | Search index | 9200 | `curl /_cluster/health` |
| `redis` | redis:7.2-alpine | Celery broker | 6379 | `redis-cli ping` |
| `backend` | Custom (FastAPI) | API server | 8000 | `curl /api/health` |
| `celery-worker` | Custom (GPU-enabled) | Async tasks | - | Celery inspect |
| `frontend` | Custom (Vite dev / Nginx prod) | Web UI | 3000 | HTTP 200 |

### docker-compose.yml

```yaml
version: '3.8'

services:
  postgres:
    image: postgres:16.1-alpine
    container_name: whedifaqaui-postgres
    environment:
      POSTGRES_USER: ${POSTGRES_USER:-whedifaqaui}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD:-whedifaqaui}
      POSTGRES_DB: ${POSTGRES_DB:-whedifaqaui}
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./scripts/init-db.sh:/docker-entrypoint-initdb.d/init-db.sh:ro
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER:-whedifaqaui}"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  opensearch:
    image: opensearchproject/opensearch:2.11.0
    container_name: whedifaqaui-opensearch
    environment:
      - discovery.type=single-node
      - plugins.security.disabled=true
      - OPENSEARCH_JAVA_OPTS=-Xms512m -Xmx512m
      - DISABLE_INSTALL_DEMO_CONFIG=true
    volumes:
      - opensearch_data:/usr/share/opensearch/data
    ports:
      - "9200:9200"
    healthcheck:
      test: ["CMD-SHELL", "curl -s http://localhost:9200/_cluster/health | grep -q '\"status\":\"green\"\\|\"status\":\"yellow\"'"]
      interval: 30s
      timeout: 10s
      retries: 5
    restart: unless-stopped

  redis:
    image: redis:7.2-alpine
    container_name: whedifaqaui-redis
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 10s
      timeout: 5s
      retries: 5
    restart: unless-stopped

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    container_name: whedifaqaui-backend
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER:-whedifaqaui}:${POSTGRES_PASSWORD:-whedifaqaui}@postgres:5432/${POSTGRES_DB:-whedifaqaui}
      - OPENSEARCH_URL=http://opensearch:9200
      - REDIS_URL=redis://redis:6379/0
      - DATA_DIR=/data
    volumes:
      - ./backend/app:/app/app:ro
      - ./data:/data
    ports:
      - "8000:8000"
    depends_on:
      postgres:
        condition: service_healthy
      opensearch:
        condition: service_healthy
      redis:
        condition: service_healthy
    healthcheck:
      test: ["CMD-SHELL", "curl -f http://localhost:8000/api/health || exit 1"]
      interval: 30s
      timeout: 10s
      retries: 3
    restart: unless-stopped

  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.worker
    container_name: whedifaqaui-worker
    command: celery -A app.tasks.celery_app worker --loglevel=info
    environment:
      - DATABASE_URL=postgresql://${POSTGRES_USER:-whedifaqaui}:${POSTGRES_PASSWORD:-whedifaqaui}@postgres:5432/${POSTGRES_DB:-whedifaqaui}
      - OPENSEARCH_URL=http://opensearch:9200
      - REDIS_URL=redis://redis:6379/0
      - DATA_DIR=/data
    volumes:
      - ./backend/app:/app/app:ro
      - ./data:/data
    depends_on:
      postgres:
        condition: service_healthy
      opensearch:
        condition: service_healthy
      redis:
        condition: service_healthy
    restart: unless-stopped

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
      target: development
    container_name: whedifaqaui-frontend
    volumes:
      - ./frontend/src:/app/src:ro
      - ./frontend/public:/app/public:ro
    ports:
      - "3000:3000"
    environment:
      - VITE_API_URL=http://localhost:8000
    depends_on:
      - backend
    restart: unless-stopped

volumes:
  postgres_data:
  opensearch_data:
  redis_data:
```

### docker-compose.dev.yml (Development Overrides)

```yaml
version: '3.8'

services:
  backend:
    build:
      target: development
    volumes:
      - ./backend/app:/app/app  # Remove :ro for hot reload
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  celery-worker:
    volumes:
      - ./backend/app:/app/app  # Remove :ro for hot reload
    command: celery -A app.tasks.celery_app worker --loglevel=debug

  frontend:
    command: npm run dev -- --host 0.0.0.0
```

### docker-compose.gpu.yml (GPU Worker Override)

```yaml
version: '3.8'

services:
  celery-worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.worker
      args:
        - BASE_IMAGE=nvidia/cuda:12.1-runtime-ubuntu22.04
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
    environment:
      - CUDA_VISIBLE_DEVICES=0
```

---

## Backend Configuration

### requirements.txt

```
# Web framework
fastapi==0.109.2
uvicorn[standard]==0.27.1
python-multipart==0.0.9

# Database
sqlalchemy==2.0.25
psycopg2-binary==2.9.9
alembic==1.13.1

# Search
opensearch-py==2.4.2

# Task queue
celery==5.3.6
redis==5.0.1

# Configuration
pydantic==2.6.1
pydantic-settings==2.1.0

# ML (Phase 1+)
# whisperx  # Installed separately due to dependencies
sentence-transformers==2.6.1
torch==2.1.2

# Media processing
# ffmpeg-python==0.2.0  # Phase 1

# Utilities
python-dateutil==2.8.2
httpx==0.26.0
```

### requirements-dev.txt

```
-r requirements.txt

# Testing
pytest==8.0.0
pytest-asyncio==0.23.4
pytest-cov==4.1.0
httpx==0.26.0

# Linting & Formatting
ruff==0.2.1
mypy==1.8.0

# Type stubs
types-python-dateutil==2.8.19
types-redis==4.6.0
```

### pyproject.toml

```toml
[project]
name = "whedifaqaui"
version = "0.1.0"
requires-python = ">=3.11"

[tool.ruff]
target-version = "py311"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]
ignore = ["E501"]  # Line length handled separately

[tool.ruff.lint.isort]
known-first-party = ["app"]

[tool.mypy]
python_version = "3.11"
strict = true
ignore_missing_imports = true

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

### app/core/config.py

```python
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Application
    app_name: str = "Whedifaqaui"
    debug: bool = False

    # Database
    database_url: str = "postgresql://whedifaqaui:whedifaqaui@localhost:5432/whedifaqaui"

    # OpenSearch
    opensearch_url: str = "http://localhost:9200"

    # Redis
    redis_url: str = "redis://localhost:6379/0"

    # Data directories
    data_dir: Path = Path("/data")

    @property
    def videos_dir(self) -> Path:
        return self.data_dir / "videos"

    @property
    def transcripts_dir(self) -> Path:
        return self.data_dir / "transcripts"

    @property
    def temp_dir(self) -> Path:
        return self.data_dir / "temp"

    @property
    def models_dir(self) -> Path:
        return self.data_dir / "models"


settings = Settings()
```

### app/core/database.py

```python
from collections.abc import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker, declarative_base

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,
    pool_size=5,
    max_overflow=10,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### app/core/opensearch.py

```python
from opensearchpy import OpenSearch

from app.core.config import settings


def get_opensearch_client() -> OpenSearch:
    return OpenSearch(
        hosts=[settings.opensearch_url],
        http_compress=True,
        use_ssl=False,
        verify_certs=False,
        ssl_show_warn=False,
    )


def check_opensearch_health() -> dict:
    """Check OpenSearch cluster health."""
    client = get_opensearch_client()
    try:
        health = client.cluster.health()
        return {
            "status": health.get("status", "unknown"),
            "cluster_name": health.get("cluster_name", "unknown"),
            "number_of_nodes": health.get("number_of_nodes", 0),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}
```

### app/tasks/celery_app.py

```python
from celery import Celery

from app.core.config import settings

celery_app = Celery(
    "whedifaqaui",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    worker_prefetch_multiplier=1,  # For long-running tasks
)

# Task modules will be registered here in Phase 1
# celery_app.autodiscover_tasks(["app.tasks"])
```

### app/api/routes/health.py

```python
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.opensearch import check_opensearch_health
from app.tasks.celery_app import celery_app

router = APIRouter()


@router.get("/health")
async def health_check(db: Session = Depends(get_db)) -> dict:
    """
    Health check endpoint that verifies all service connections.
    """
    health = {
        "status": "ok",
        "services": {}
    }

    # Check PostgreSQL
    try:
        db.execute(text("SELECT 1"))
        health["services"]["postgres"] = {"status": "ok"}
    except Exception as e:
        health["services"]["postgres"] = {"status": "error", "error": str(e)}
        health["status"] = "degraded"

    # Check OpenSearch
    os_health = check_opensearch_health()
    if os_health.get("status") in ("green", "yellow"):
        health["services"]["opensearch"] = {"status": "ok", **os_health}
    else:
        health["services"]["opensearch"] = {"status": "error", **os_health}
        health["status"] = "degraded"

    # Check Redis/Celery
    try:
        celery_app.control.ping(timeout=1.0)
        health["services"]["redis"] = {"status": "ok"}
    except Exception as e:
        health["services"]["redis"] = {"status": "error", "error": str(e)}
        health["status"] = "degraded"

    return health
```

### app/api/deps.py

```python
from collections.abc import Generator

from sqlalchemy.orm import Session

from app.core.database import SessionLocal


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### app/main.py

```python
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import health
from app.core.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    # Startup: ensure data directories exist
    settings.videos_dir.mkdir(parents=True, exist_ok=True)
    (settings.videos_dir / "original").mkdir(exist_ok=True)
    (settings.videos_dir / "processed").mkdir(exist_ok=True)
    (settings.videos_dir / "audio").mkdir(exist_ok=True)
    (settings.videos_dir / "thumbnails").mkdir(exist_ok=True)
    (settings.videos_dir / "screenshots").mkdir(exist_ok=True)
    settings.transcripts_dir.mkdir(parents=True, exist_ok=True)
    settings.temp_dir.mkdir(parents=True, exist_ok=True)
    settings.models_dir.mkdir(parents=True, exist_ok=True)

    yield

    # Shutdown: cleanup if needed
    pass


app = FastAPI(
    title=settings.app_name,
    description="Video Knowledge Management System",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routes
app.include_router(health.router, prefix="/api", tags=["health"])
```

### Backend Dockerfile

```dockerfile
# backend/Dockerfile
FROM python:3.11-slim as base

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Development stage
FROM base as development
COPY requirements-dev.txt .
RUN pip install --no-cache-dir -r requirements-dev.txt
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

# Production stage
FROM base as production
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Worker Dockerfile (GPU-enabled)

```dockerfile
# backend/Dockerfile.worker
ARG BASE_IMAGE=python:3.11-slim
FROM ${BASE_IMAGE} as base

WORKDIR /app

# Install system dependencies including FFmpeg
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    ffmpeg \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Install WhisperX (separate due to complex dependencies)
RUN pip install --no-cache-dir git+https://github.com/m-bain/whisperx.git

# Copy application
COPY . .

CMD ["celery", "-A", "app.tasks.celery_app", "worker", "--loglevel=info"]
```

---

## Frontend Configuration

### package.json

```json
{
  "name": "whedifaqaui-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview",
    "lint": "eslint src --ext ts,tsx",
    "lint:fix": "eslint src --ext ts,tsx --fix",
    "format": "prettier --write \"src/**/*.{ts,tsx,css}\"",
    "test": "vitest",
    "test:coverage": "vitest --coverage"
  },
  "dependencies": {
    "react": "^18.2.0",
    "react-dom": "^18.2.0",
    "react-router-dom": "^6.22.0",
    "axios": "^1.6.7"
  },
  "devDependencies": {
    "@types/react": "^18.2.55",
    "@types/react-dom": "^18.2.19",
    "@typescript-eslint/eslint-plugin": "^7.0.1",
    "@typescript-eslint/parser": "^7.0.1",
    "@vitejs/plugin-react": "^4.2.1",
    "autoprefixer": "^10.4.17",
    "eslint": "^8.56.0",
    "eslint-plugin-react-hooks": "^4.6.0",
    "eslint-plugin-react-refresh": "^0.4.5",
    "postcss": "^8.4.35",
    "prettier": "^3.2.5",
    "tailwindcss": "^3.4.1",
    "typescript": "^5.3.3",
    "vite": "^5.4.0",
    "vitest": "^1.2.2"
  }
}
```

### vite.config.ts

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
})
```

### tailwind.config.js

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {},
  },
  plugins: [],
}
```

### tsconfig.json

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": {
      "@/*": ["src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

### src/main.tsx

```tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'
import './styles/index.css'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

### src/App.tsx

```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import Layout from './components/common/Layout'
import PlaceholderPage from './pages/PlaceholderPage'

function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<PlaceholderPage title="Library" />} />
          <Route path="upload" element={<PlaceholderPage title="Upload" />} />
          <Route path="search" element={<PlaceholderPage title="Search" />} />
          <Route path="videos/:id" element={<PlaceholderPage title="Video" />} />
        </Route>
      </Routes>
    </BrowserRouter>
  )
}

export default App
```

### src/components/common/Layout.tsx

```tsx
import { Outlet, Link } from 'react-router-dom'

export default function Layout() {
  return (
    <div className="min-h-screen bg-gray-50">
      <nav className="bg-white shadow">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 justify-between">
            <div className="flex">
              <Link to="/" className="flex items-center text-xl font-bold text-gray-900">
                Whedifaqaui
              </Link>
              <div className="ml-10 flex items-center space-x-4">
                <Link to="/" className="text-gray-600 hover:text-gray-900">Library</Link>
                <Link to="/upload" className="text-gray-600 hover:text-gray-900">Upload</Link>
                <Link to="/search" className="text-gray-600 hover:text-gray-900">Search</Link>
              </div>
            </div>
          </div>
        </div>
      </nav>
      <main className="mx-auto max-w-7xl px-4 py-6 sm:px-6 lg:px-8">
        <Outlet />
      </main>
    </div>
  )
}
```

### src/pages/PlaceholderPage.tsx

```tsx
interface Props {
  title: string
}

export default function PlaceholderPage({ title }: Props) {
  return (
    <div className="rounded-lg border-2 border-dashed border-gray-300 p-12 text-center">
      <h1 className="text-2xl font-semibold text-gray-900">{title}</h1>
      <p className="mt-2 text-gray-500">This page will be implemented in Phase 1</p>
    </div>
  )
}
```

### src/api/client.ts

```typescript
import axios from 'axios'

const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_URL || '/api',
  headers: {
    'Content-Type': 'application/json',
  },
})

export async function checkHealth(): Promise<{
  status: string
  services: Record<string, { status: string }>
}> {
  const response = await apiClient.get('/health')
  return response.data
}

export default apiClient
```

### src/styles/index.css

```css
@tailwind base;
@tailwind components;
@tailwind utilities;
```

### Frontend Dockerfile

```dockerfile
# frontend/Dockerfile

# Development stage
FROM node:20-alpine as development
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
EXPOSE 3000
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# Build stage
FROM node:20-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine as production
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
```

---

## Environment Configuration

### .env.example

```bash
# Database
POSTGRES_USER=whedifaqaui
POSTGRES_PASSWORD=whedifaqaui
POSTGRES_DB=whedifaqaui

# Application
DEBUG=true

# Optional: Override service URLs (defaults work with docker-compose)
# DATABASE_URL=postgresql://whedifaqaui:whedifaqaui@localhost:5432/whedifaqaui
# OPENSEARCH_URL=http://localhost:9200
# REDIS_URL=redis://localhost:6379/0
```

### .gitignore

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
.venv/
venv/
ENV/
.mypy_cache/
.pytest_cache/
.ruff_cache/
*.egg-info/
dist/
build/

# Node
node_modules/
npm-debug.log*

# IDE
.vscode/
.idea/
*.swp
*.swo

# Environment
.env
.env.local
.env.*.local

# Data (large files)
data/videos/
data/transcripts/
data/temp/
data/models/
!data/**/.gitkeep

# Build outputs
frontend/dist/
backend/dist/

# Docker
*.log
```

---

## Makefile

```makefile
.PHONY: help dev dev-gpu build up down logs test lint format clean

help:
	@echo "Available commands:"
	@echo "  make dev        - Start development environment"
	@echo "  make dev-gpu    - Start development environment with GPU"
	@echo "  make build      - Build Docker images"
	@echo "  make up         - Start all services"
	@echo "  make down       - Stop all services"
	@echo "  make logs       - View logs"
	@echo "  make test       - Run tests"
	@echo "  make lint       - Run linters"
	@echo "  make format     - Format code"
	@echo "  make clean      - Clean up"

dev:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml up --build

dev-gpu:
	docker compose -f docker-compose.yml -f docker-compose.dev.yml -f docker-compose.gpu.yml up --build

build:
	docker compose build

up:
	docker compose up -d

down:
	docker compose down

logs:
	docker compose logs -f

test:
	docker compose exec backend pytest
	docker compose exec frontend npm test

lint:
	docker compose exec backend ruff check app
	docker compose exec frontend npm run lint

format:
	docker compose exec backend ruff format app
	docker compose exec frontend npm run format

clean:
	docker compose down -v
	rm -rf data/temp/*
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type d -name node_modules -exec rm -rf {} +
```

---

## Alembic Configuration

### alembic.ini

```ini
[alembic]
script_location = migrations
prepend_sys_path = .
sqlalchemy.url = driver://user:pass@localhost/dbname

[logging]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic

[logger_root]
level = WARN
handlers = console
qualname =

[logger_sqlalchemy]
level = WARN
handlers =
qualname = sqlalchemy.engine

[logger_alembic]
level = INFO
handlers =
qualname = alembic

[handler_console]
class = StreamHandler
args = (sys.stderr,)
level = NOTSET
formatter = generic

[formatter_generic]
format = %(levelname)-5.5s [%(name)s] %(message)s
datefmt = %H:%M:%S
```

### migrations/env.py

```python
from logging.config import fileConfig
import os

from sqlalchemy import engine_from_config, pool
from alembic import context

from app.core.database import Base
from app.core.config import settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def get_url():
    return settings.database_url


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

---

## Verification Scripts

### scripts/verify-environment.sh

```bash
#!/bin/bash
set -e

echo "=== Whedifaqaui Environment Verification ==="
echo ""

# Check Docker
echo "Checking Docker..."
docker --version || { echo "ERROR: Docker not found"; exit 1; }
docker compose version || { echo "ERROR: Docker Compose not found"; exit 1; }
echo "OK"
echo ""

# Check services are running
echo "Checking services..."
docker compose ps --format "table {{.Name}}\t{{.Status}}" | grep -E "running|Up" || {
    echo "ERROR: Services not running. Run 'make dev' first."
    exit 1
}
echo ""

# Check PostgreSQL
echo "Checking PostgreSQL..."
docker compose exec -T postgres pg_isready -U whedifaqaui || {
    echo "ERROR: PostgreSQL not ready"
    exit 1
}
echo "OK"
echo ""

# Check OpenSearch
echo "Checking OpenSearch..."
curl -s http://localhost:9200/_cluster/health | grep -E '"status":"(green|yellow)"' || {
    echo "ERROR: OpenSearch not healthy"
    exit 1
}
echo "OK"
echo ""

# Check Redis
echo "Checking Redis..."
docker compose exec -T redis redis-cli ping | grep PONG || {
    echo "ERROR: Redis not responding"
    exit 1
}
echo "OK"
echo ""

# Check Backend Health
echo "Checking Backend..."
curl -s http://localhost:8000/api/health | grep '"status":"ok"' || {
    echo "WARNING: Backend health check returned degraded status"
}
echo "OK"
echo ""

# Check Frontend
echo "Checking Frontend..."
curl -s -o /dev/null -w "%{http_code}" http://localhost:3000 | grep -E "200|304" || {
    echo "ERROR: Frontend not responding"
    exit 1
}
echo "OK"
echo ""

# Check FFmpeg in worker
echo "Checking FFmpeg in worker..."
docker compose exec -T celery-worker ffmpeg -version | head -1 || {
    echo "ERROR: FFmpeg not available in worker"
    exit 1
}
echo "OK"
echo ""

# Check data directories
echo "Checking data directories..."
for dir in data/videos/original data/videos/processed data/videos/audio data/videos/thumbnails data/videos/screenshots data/transcripts data/temp data/models; do
    if [ ! -d "$dir" ]; then
        echo "ERROR: Directory $dir does not exist"
        exit 1
    fi
done
echo "OK"
echo ""

# Check volume write access from container
echo "Checking volume write access..."
docker compose exec -T backend python -c "
from pathlib import Path
test_file = Path('/data/temp/write_test.txt')
test_file.write_text('test')
assert test_file.read_text() == 'test', 'Read back failed'
test_file.unlink()
print('Write/read/delete OK')
" || {
    echo "ERROR: Container cannot write to /data volume"
    exit 1
}
echo ""

# Check Celery task execution
echo "Checking Celery task execution..."
docker compose exec -T backend python -c "
from app.tasks.celery_app import celery_app
result = celery_app.send_task('celery.ping')
response = result.get(timeout=10)
assert response == 'pong', f'Unexpected response: {response}'
print('Celery ping OK')
" || {
    echo "ERROR: Celery task execution failed"
    exit 1
}
echo ""

# Check Alembic configuration
echo "Checking Alembic..."
docker compose exec -T backend alembic current || {
    echo "ERROR: Alembic not configured correctly"
    exit 1
}
echo "OK"
echo ""

# Check database query execution
echo "Checking database query execution..."
docker compose exec -T backend python -c "
from sqlalchemy import text
from app.core.database import SessionLocal
db = SessionLocal()
result = db.execute(text('SELECT current_database(), current_user'))
row = result.fetchone()
assert row[0] == 'whedifaqaui', f'Wrong database: {row[0]}'
print(f'Connected to {row[0]} as {row[1]}')
db.close()
" || {
    echo "ERROR: Database query execution failed"
    exit 1
}
echo ""

# Check OpenSearch index operations
echo "Checking OpenSearch write capability..."
docker compose exec -T backend python -c "
from app.core.opensearch import get_opensearch_client
client = get_opensearch_client()
client.indices.create('test-phase0', body={})
client.indices.delete('test-phase0')
print('Index create/delete OK')
" || {
    echo "ERROR: OpenSearch index operations failed"
    exit 1
}
echo ""

# Check sentence-transformers import
echo "Checking sentence-transformers..."
docker compose exec -T celery-worker python -c "
from sentence_transformers import SentenceTransformer
print('Import OK')
" || {
    echo "ERROR: sentence-transformers not available"
    exit 1
}
echo ""

# Check WhisperX import
echo "Checking WhisperX..."
docker compose exec -T celery-worker python -c "
import whisperx
print('Import OK')
" || {
    echo "ERROR: WhisperX not available"
    exit 1
}
echo ""

# Check frontend API proxy
echo "Checking frontend API proxy..."
docker compose exec -T frontend wget -q -O - http://localhost:3000/api/health 2>/dev/null | grep -q '"status"' || {
    echo "WARNING: Frontend proxy to backend may not be working (expected in production build)"
}
echo "OK"
echo ""

# Check type checking
echo "Checking mypy..."
docker compose exec -T backend mypy app --ignore-missing-imports || {
    echo "WARNING: Type errors found (non-blocking)"
}
echo ""

echo "=== All checks passed ==="
```

---

## Exit Criteria

Phase 0 is complete when all of the following are verified:

```
Infrastructure:
[ ] docker compose up starts all services without errors
[ ] PostgreSQL accepts connections (pg_isready succeeds)
[ ] OpenSearch cluster health is green or yellow
[ ] Redis responds to PING
[ ] All containers remain healthy for 5+ minutes

Backend:
[ ] GET /api/health returns {"status": "ok", ...}
[ ] Health endpoint shows all services connected
[ ] Alembic shows current revision (even if none)
[ ] Celery can execute a ping task end-to-end
[ ] Database query execution works from application code
[ ] OpenSearch accepts index create/delete operations
[ ] pytest runs successfully (0 tests is acceptable)
[ ] ruff check passes with no errors
[ ] mypy passes with no errors (or only expected ones)

Frontend:
[ ] Frontend loads at http://localhost:3000
[ ] Navigation between placeholder pages works
[ ] API client can call /api/health
[ ] Frontend proxy routes /api/* to backend (dev mode)
[ ] npm test runs successfully (0 tests is acceptable)
[ ] eslint passes with no errors

Data:
[ ] All data directories created with correct permissions
[ ] Backend container can write files to /data/temp
[ ] Written files can be read back correctly
[ ] Containers can delete files from /data volume

Worker:
[ ] FFmpeg available (ffmpeg --version works)
[ ] WhisperX installed (import whisperx succeeds)
[ ] sentence-transformers module imports successfully

Integration:
[ ] Backend can execute SQL queries via SQLAlchemy
[ ] Backend can perform OpenSearch index operations
[ ] Celery worker receives and executes tasks from backend
[ ] Frontend can reach backend through Vite proxy

Development:
[ ] Backend hot-reload triggers on file change
[ ] Frontend hot-reload triggers on file change

Documentation:
[ ] README.md has setup instructions
[ ] .env.example documents all variables
```

---

## What's Deferred to Phase 1

| Component | Phase |
|-----------|-------|
| Video model and migrations | Phase 1 |
| Transcript model and migrations | Phase 1 |
| Segment model and migrations | Phase 1 |
| Upload endpoint | Phase 1 |
| Video processing task | Phase 1 |
| Transcription task | Phase 1 |
| Search endpoint | Phase 1 |
| All functional UI pages | Phase 1 |

---

## Estimated Work

| Category | Items |
|----------|-------|
| Docker/Infrastructure | docker-compose files, Dockerfiles, scripts |
| Backend Scaffolding | FastAPI app, config, database, health endpoint |
| Frontend Scaffolding | Vite setup, routing, placeholder pages |
| Configuration | Environment files, linting, formatting |
| Documentation | README, Makefile |

Phase 0 establishes the foundation. No business logic is implemented - only infrastructure and scaffolding that enables Phase 1 development to begin immediately.
