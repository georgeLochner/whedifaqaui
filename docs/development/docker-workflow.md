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
│                                                              │
└──────────────────┬──────────────────────────────────────────┘
                   │ Volume Mount
                   ▼
┌─────────────────────────────────────────────────────────────┐
│                  Docker Container                            │
│                                                              │
│  /app/  ← Maps to host, changes appear immediately          │
│                                                              │
│  Dependencies: Python packages, Node modules, etc.           │
│  Running Processes: Web servers, workers, etc.               │
└─────────────────────────────────────────────────────────────┘
```

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
