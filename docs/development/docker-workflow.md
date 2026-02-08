# Docker Development Workflow

This document explains the Docker-based development workflow for agentic development projects, focusing on the distinction between development and production modes.

---

## The Core Pattern

**Principle**: Dependencies run in containers. Source code lives on the host and is volume-mapped for immediate reflection of changes.

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

## Two Modes: Development vs Production

### Development Mode (Recommended for Agent Work)

**Purpose**: Fast iteration during development

**Configuration**: `docker-compose.yml` + `docker-compose.dev.yml`

**Key Characteristics**:
- ✅ Source code volume-mapped from host
- ✅ Hot reload enabled (server watches for file changes)
- ✅ **No rebuild needed** when editing code
- ✅ Changes reflect immediately in running containers
- ✅ Fast iteration cycle (~seconds to see changes)

**When to use**: All development work, testing, debugging, agent execution

**How to start**:
```bash
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

---

### Production Mode (For Final Verification)

**Purpose**: Test production build before deployment

**Configuration**: `docker-compose.yml` only

**Key Characteristics**:
- 📦 Source code copied into image at build time (`COPY . /app`)
- 📦 No volume mounts for application code
- ⚠️ **Rebuild required** after any code change
- ⚠️ Slow iteration cycle (~minutes to rebuild)
- ✅ Matches production deployment exactly

**When to use**: Final integration testing, pre-deployment verification

**How to start**:
```bash
docker compose up -d
```

**After code changes**:
```bash
docker compose build <service>  # Rebuild the image
docker compose up -d <service>  # Restart with new image
```

---

## File Structure

### Base Configuration: `docker-compose.yml`

```yaml
services:
  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    environment:
      - DATABASE_URL=postgresql://...
    ports:
      - "8000:8000"
    depends_on:
      - postgres
    # Note: No volume mount for /app
    # Code is baked in via Dockerfile COPY
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000

  postgres:
    image: postgres:16
    environment:
      POSTGRES_DB: mydb
    volumes:
      - postgres_data:/var/lib/postgresql/data  # Data persists
    ports:
      - "5432:5432"

volumes:
  postgres_data:
```

### Development Overrides: `docker-compose.dev.yml`

```yaml
services:
  backend:
    volumes:
      - ./backend:/app           # Mount source code
      - /app/__pycache__         # Exclude cache
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    # --reload flag enables hot reload

  frontend:
    volumes:
      - ./frontend:/app
      - /app/node_modules        # Preserve node_modules in container
```

**Key points**:
- Volume mount: `./backend:/app` makes host code visible in container
- Exclude patterns: `/app/__pycache__` prevents cache conflicts
- Hot reload: `--reload` flag watches for file changes

---

## How Development Mode Works

### 1. Start Services

```bash
# Start all services with development overrides
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

Docker Compose merges the two files:
- Base configuration from `docker-compose.yml`
- Development overrides from `docker-compose.dev.yml`

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
# Run tests inside the container against the updated code
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

**Important**: This only works when the frontend container runs the `development` stage (node-based). If the container is running the `production` stage (nginx), there is no `npm` available — see [Frontend Development Architecture](#frontend-development-architecture) below.

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

The frontend uses a **multi-stage Dockerfile** with separate stages for development and production:

```dockerfile
# Development stage — node + vite dev server (hot reload)
FROM node:20-alpine as development
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
CMD ["npm", "run", "dev", "--", "--host", "0.0.0.0"]

# Build stage — produces static assets
FROM node:20-alpine as build
WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage — nginx serves static files
FROM nginx:alpine as production
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
```

**In development mode**, `docker-compose.yml` targets the `development` stage:

```yaml
frontend:
    build:
      context: ./frontend
      target: development    # ← uses node, NOT nginx
```

And `docker-compose.dev.yml` overrides the command for hot reload:

```yaml
frontend:
    command: npm run dev -- --host 0.0.0.0
```

This gives you:
- A **node container** running vite's dev server with hot reload
- Source code volume-mapped from host — changes reflect instantly
- `npm install` works inside the container (node/npm available)
- Hot Module Replacement (HMR) for instant browser updates

**Common mistake**: If the Dockerfile only has `build` and `production` stages (missing the `development` stage), the container runs nginx. In that case:
- Volume mounts are useless (nginx serves from `/usr/share/nginx/html`, not `/app`)
- `npm` is not available (nginx:alpine has no node)
- Every change requires a full image rebuild
- Hot reload does not work

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
- Node packages — Dockerfile runs `npm ci` (from `package.json` + `package-lock.json`)
- Database schema — Alembic migrations (committed to git)
- Infrastructure — Docker Compose recreates postgres, redis, opensearch

**What is NOT restored:**
- Database data (unless volumes survived the crash)
- Uploaded files / processed media
- OpenSearch indices (need re-indexing)

---

## How Production Mode Works

### 1. Start Services (Production Mode)

```bash
# Start without dev overrides
docker compose up -d
```

### 2. Code is Baked Into Image

From `backend/Dockerfile`:
```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install -r requirements.txt

# Copy source code into image
COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

The `COPY . .` command bakes the code into the image at build time.

### 3. Edit Code on Host

```bash
vim ./backend/app/api/routes/videos.py
```

### 4. Changes DO NOT Reflect

```
┌─────────────────────────────────────────────────────────────┐
│ Host: ./backend/app/api/routes/videos.py                    │
│       ↓ (file modified)                                      │
│       ✗ (not mounted)                                        │
│                                                              │
│ Container: /app/app/api/routes/videos.py                    │
│       ↑ (still has old code from image build)               │
│                                                              │
│ Result: Running container sees no change                    │
└─────────────────────────────────────────────────────────────┘
```

**Rebuild required!**

### 5. Rebuild and Restart

```bash
# Rebuild the image with new code
docker compose build backend

# Restart container with new image
docker compose up -d backend

# Or do both in one command:
docker compose up -d --build backend
```

### 6. Force Rebuild Without Cache (if needed)

If Docker's layer cache doesn't detect changes:

```bash
docker compose build --no-cache backend
docker compose up -d backend
```

---

## Common Workflows

### Starting Fresh (Development Mode)

```bash
# 1. Start all services with dev mode
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

# Changes appear immediately (if hot reload enabled)
# Otherwise, restart just that service:
docker compose restart backend

# Test your changes
docker compose exec backend pytest tests/unit/test_videos.py

# Commit when verified
git add backend/app/api/routes/videos.py
git commit -m "Add video upload"
```

### Verifying Production Build

```bash
# Stop dev mode services
docker compose -f docker-compose.yml -f docker-compose.dev.yml down

# Start production mode
docker compose up -d

# Run integration tests
docker compose exec backend pytest tests/integration/

# If tests pass, build is ready for deployment
```

### Troubleshooting: Code Changes Not Appearing

**Symptom**: You edited code but the running container still behaves the old way.

**Diagnosis**:
```bash
# Check if you're in dev mode
docker compose ps
# Look for volume mounts in the output

# Check what code is actually in the container
docker compose exec backend cat /app/app/api/routes/videos.py
```

**Solutions**:

1. **Not using dev mode** - Restart with dev compose file:
   ```bash
   docker compose down
   docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
   ```

2. **Hot reload not working** - Restart the service:
   ```bash
   docker compose restart backend
   ```

3. **Using production mode** - Rebuild is required:
   ```bash
   docker compose build backend
   docker compose up -d backend
   ```

4. **Docker cache issue** - Force rebuild:
   ```bash
   docker compose build --no-cache backend
   docker compose up -d backend
   ```

---

## Best Practices for Agents

### ✅ DO

- **Always start in development mode** for task work
- **Edit code on host filesystem** (not inside containers)
- **Run tests inside containers** via `docker compose exec`
- **Verify changes work** before committing
- **Check logs** if behavior unexpected: `docker compose logs <service>`

### ❌ DON'T

- **Don't use production mode** for development work (too slow)
- **Don't edit files inside containers** (changes will be lost)
- **Don't commit without testing** in the container environment
- **Don't mix modes** (pick dev or prod, don't switch mid-task)

### When Something Goes Wrong

1. **Check which mode you're in**: `docker compose ps`
2. **Verify code in container**: `docker compose exec <service> cat /path/to/file`
3. **Check logs**: `docker compose logs -f <service>`
4. **Restart service if needed**: `docker compose restart <service>`
5. **Last resort**: Stop everything and start fresh in dev mode

---

## Advanced: Customizing for Your Project

### Adding a New Service

1. **Add to base `docker-compose.yml`**:
   ```yaml
   myservice:
     build: ./myservice
     ports:
       - "8080:8080"
     depends_on:
       - postgres
   ```

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

---

## Summary

| Aspect | Development Mode | Production Mode |
|--------|------------------|-----------------|
| **Usage** | `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d` | `docker compose up -d` |
| **Code location** | Volume-mapped from host | Baked into image |
| **After code change** | Automatic reload (~seconds) | Rebuild required (~minutes) |
| **Use case** | Development, testing, agent work | Final verification, deployment |
| **Rebuild needed?** | ❌ No | ✅ Yes |
| **Speed** | ⚡ Fast | 🐢 Slow |

**Default for agents**: Always use **Development Mode** unless explicitly testing production builds.
