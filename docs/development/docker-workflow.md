# Docker Development Workflow

This document explains the Docker-based development workflow for agentic development projects.

---

## The Core Pattern

**Principle**: Dependencies run in containers. Source code lives on the host and is volume-mapped for immediate reflection of changes.

### Dependency Pre-Loading

All dependencies listed in the technology stack (e.g., `technology-stack.md`) across **all planned phases** must be installed into the Docker images during the initial environment setup (Phase 0 or equivalent scaffolding). This means:

- `requirements.txt` includes every Python package from the technology stack — not just the packages needed for scaffolding
- `package.json` includes every npm package from the technology stack
- The Dockerfile installs any required system packages (e.g., `ffmpeg`, `libsndfile1`)

**Why**: Feature agents should never need to install dependencies. When an agent starts working on a feature, every import should already work. Dependency management during feature development is a distraction that wastes agent context and risks inconsistent environments.

**The fast-path install** (`docker compose exec ... pip install`) exists for cases where a dependency was missed or a new one is discovered during development. It is a recovery mechanism, not the normal workflow.

```
┌─────────────────────────────────────────────────────────────┐
│                      Host Filesystem                         │
│                                                              │
│  ./backend/app/           ← Agent edits code here            │
│  ./frontend/src/                                             │
│  requirements.txt         ← Dependency manifests             │
│  package.json                                                │
│                                                              │
└──────────────────┬──────────────────────────────────────────┘
                   │ Volume Mount (source code)
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                  Docker Container                            │
│                                                              │
│  /app/  ← Maps to host, changes appear immediately          │
│                                                              │
│  Dependencies: Installed in container filesystem             │
│    • Baked in at build time (Dockerfile RUN pip/npm install) │
│    • Can be updated live: docker compose exec ... install    │
│  Running Processes: Web servers, workers, etc.               │
└─────────────────────────────────────────────────────────────┘
```

There are two types of changes during development, each with a different workflow:

| Change Type | Workflow | Rebuild? |
|-------------|----------|----------|
| **Source code** | Edit on host → auto-reflected via volume mount | No |
| **Dependencies** | Edit manifest on host → install inside container | No |
| **Dockerfile / system packages** | Edit Dockerfile → rebuild image | Yes |

---

## Configuration

Development uses two Docker Compose files merged together:

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### Base Configuration: `docker-compose.yml`

Defines all services, build contexts, ports, health checks, and dependencies.

### Development Overrides: `docker-compose.dev.yml`

Adds volume mounts and hot-reload commands:

```yaml
services:
  backend:
    volumes:
      - ./backend:/app           # Mount source code
      - /app/__pycache__         # Exclude cache
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  frontend:
    command: npm run dev -- --host 0.0.0.0
```

**Key points**:
- Volume mount: `./backend:/app` makes host code visible in container
- Exclude patterns: `/app/__pycache__` prevents cache conflicts
- Hot reload: `--reload` flag watches for file changes
- Frontend: `npm run dev` runs vite's dev server with Hot Module Replacement

---

## How It Works

### 1. Start Services

```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

### 2. Edit Code on Host

```bash
# Agent or human edits code on host filesystem
vim ./backend/app/api/routes/videos.py
```

### 3. Changes Reflect Immediately

```
┌─────────────────────────────────────────────────────────────┐
│ Host: ./backend/app/api/routes/videos.py                    │
│       ↓ (file modified)                                      │
│       ↓                                                      │
│ Container: /app/app/api/routes/videos.py                    │
│       ↓ (change detected by --reload)                       │
│       ↓                                                      │
│ Server: Automatically reloads application                    │
│       ↓                                                      │
│ Result: New code running in ~2 seconds                      │
└─────────────────────────────────────────────────────────────┘
```

**No rebuild needed!** The server watches for file changes and reloads automatically.

### 4. Test Changes

```bash
docker compose exec backend pytest tests/unit/test_videos.py -v
```

### 5. Commit When Verified

```bash
git add backend/app/api/routes/videos.py
git commit -m "Add video upload endpoint"
```

---

## Managing Dependencies (Without Rebuilding)

Source code changes are handled by volume mounts. But what about adding a new Python package or npm module?

### The Two-Path Model

Dependencies are defined in manifest files (`requirements.txt`, `package.json`) which live on the host and are committed to git. These manifests are installed in two situations:

1. **At image build time** — the Dockerfile runs `pip install` / `npm ci`, creating the baseline environment
2. **During development** — `docker compose exec` installs into the running container for immediate use

Both paths read from the same manifest files. The Dockerfile is the canonical source for reproducible builds; the exec command is a fast-path shortcut during development.

### Adding a Backend Dependency

```bash
# 1. Edit requirements.txt on host (add the new package)
#    e.g., add "boto3==1.34.0"

# 2. Install inside the running container (fast, ~seconds)
docker compose exec backend pip install -r requirements.txt

# 3. Verify it works
docker compose exec backend python -c "import boto3; print(boto3.__version__)"

# 4. Commit requirements.txt
git add backend/requirements.txt
```

### Adding a Frontend Dependency

```bash
# 1. Edit package.json on host (add the new package)
#    e.g., add "lucide-react": "^0.300.0" to dependencies

# 2. Install inside the running container (fast, ~seconds)
docker compose exec frontend npm install

# 3. Verify it works
docker compose exec frontend node -e "require('lucide-react')"

# 4. Commit package.json and package-lock.json
git add frontend/package.json frontend/package-lock.json
```

### What Happens on Recovery / Fresh Setup

If the container is destroyed (crash, `docker compose down`, fresh clone), the exec-installed packages are lost. Recovery is simply:

```bash
docker compose build                    # Dockerfile installs all deps from manifests
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
docker compose exec backend alembic upgrade head
```

This works because the manifest files (`requirements.txt`, `package.json`) were committed to git. The Dockerfile picks them up and installs everything from scratch.

### When You MUST Rebuild

Some changes cannot be applied with `exec` — they require `docker compose build`:

| Change | Why rebuild is needed |
|--------|----------------------|
| Dockerfile changes | Build instructions changed |
| System packages (apt-get) | Only installable during build |
| Base image changes | New OS/runtime layer |
| Build-time configuration | ENV, ARG, multi-stage targets |

For everything else (source code, Python/Node packages), use the fast path.

---

## Frontend Development Architecture

The frontend Dockerfile is a single-stage `node:20-alpine` image that runs the vite dev server with hot reload. The `docker-compose.dev.yml` overrides the command and adds volume mounts:

```yaml
frontend:
    volumes:
      - ./frontend:/app
      - /app/node_modules    # Preserve container's node_modules
    command: npm run dev -- --host 0.0.0.0
```

This gives you:
- A **node container** running vite's dev server with hot reload
- Source code volume-mapped from host — changes reflect instantly
- `npm install` works inside the container (node/npm available)
- Hot Module Replacement (HMR) for instant browser updates

---

## Recovery From Scratch

If the development environment is completely lost (server crash, fresh machine, etc.), here is the full recovery process:

```bash
# 1. Clone the repo (source code + manifests + Dockerfiles)
git clone <repo-url> && cd <project>

# 2. Build all images (installs deps from committed manifests)
docker compose build

# 3. Start in development mode
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 4. Wait for infrastructure services to be healthy
docker compose ps   # postgres, redis, opensearch should show "healthy"

# 5. Run database migrations
docker compose exec backend alembic upgrade head

# 6. Verify
curl -s http://localhost:8000/api/health    # Backend
curl -s http://localhost:3000               # Frontend
```

**What gets restored:**
- Source code — from git
- Python packages — Dockerfile runs `pip install -r requirements.txt`
- Node packages — Dockerfile runs `npm install` (from `package.json`)
- Database schema — Alembic migrations (committed to git)
- Infrastructure — Docker Compose recreates postgres, redis, opensearch

**What is NOT restored:**
- Database data (unless volumes survived the crash)
- Uploaded files / processed media
- OpenSearch indices (need re-indexing)

---

## Common Workflows

### Starting Fresh

```bash
# 1. Start all services
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# 2. Check all services are healthy
docker compose ps

# 3. Watch logs (optional)
docker compose logs -f backend

# 4. Run initial migrations or setup
docker compose exec backend alembic upgrade head
```

### Daily Development Work

```bash
# Edit code on host (use your IDE, vim, etc.)
vim backend/app/api/routes/videos.py

# Changes appear immediately (hot reload)
# If not, restart the service:
docker compose restart backend

# Test your changes
docker compose exec backend pytest tests/unit/test_videos.py

# Commit when verified
git add backend/app/api/routes/videos.py
git commit -m "Add video upload"
```

### Troubleshooting: Code Changes Not Appearing

**Symptom**: You edited code but the running container still behaves the old way.

**Diagnosis**:
```bash
# Check what code is actually in the container
docker compose exec backend cat /app/app/api/routes/videos.py
```

**Solutions**:

1. **Hot reload not triggered** — Restart the service:
   ```bash
   docker compose restart backend
   ```

2. **Volume mount not active** — Restart with dev compose file:
   ```bash
   docker compose down
   docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
   ```

---

## Best Practices for Agents

### ✅ DO

- **Edit code on host filesystem** (not inside containers)
- **Install dependencies via exec** (not via rebuild)
- **Run tests inside containers** via `docker compose exec`
- **Verify changes work** before committing
- **Check logs** if behavior unexpected: `docker compose logs <service>`

### ❌ DON'T

- **Don't rebuild images** to install Python/Node packages
- **Don't edit files inside containers** (changes will be lost)
- **Don't commit without testing** in the container environment

### When Something Goes Wrong

1. **Verify code in container**: `docker compose exec <service> cat /path/to/file`
2. **Check logs**: `docker compose logs -f <service>`
3. **Restart service if needed**: `docker compose restart <service>`
4. **Last resort**: Stop everything and start fresh:
   ```bash
   docker compose down
   docker compose build
   docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
   ```

---

## Advanced: Customizing for Your Project

### Adding a New Service

1. **Add to base `docker-compose.yml`** with build context, ports, health checks

2. **Add dev overrides in `docker-compose.dev.yml`**:
   ```yaml
   myservice:
     volumes:
       - ./myservice:/app
     command: <command-with-hot-reload-flag>
   ```

### Different Languages

| Language | Hot Reload Flag | Example Command |
|----------|-----------------|-----------------|
| Python | `--reload` | `uvicorn app.main:app --reload` |
| Node.js | Built into dev server | `npm run dev` or `nodemon` |
| Go | Use `air` or `reflex` | `air` or `reflex -r '\.go$' -s go run .` |

### Excluding Files from Volume Mount

Some files should live only in the container:

```yaml
volumes:
  - ./backend:/app
  - /app/__pycache__        # Python cache
  - /app/.pytest_cache      # Pytest cache
  - /app/node_modules       # Node dependencies (frontend)
```
