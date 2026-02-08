# Development Troubleshooting

Common issues and solutions for autonomous agentic development in Docker environments.

---

## Docker Issues

### Code Changes Not Appearing in Container

**Symptoms**:
- Modified code on host
- Container still uses old behavior
- Tests fail for new functionality

**Diagnosis**:
```bash
# Check what code is actually in the container
docker compose exec backend cat /app/app/api/routes/videos.py

# Check if volume mounts are active
docker compose ps
docker inspect <container-name> | grep -A10 Mounts
```

**Solutions**:

1. **Hot reload not triggered**:
   ```bash
   docker compose restart backend
   ```

2. **Volume mount not active** — Restart with dev compose file:
   ```bash
   docker compose down
   docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
   ```

---

### Service Won't Start

**Symptoms**:
- `docker compose up -d` completes but service not running
- `docker compose ps` shows service as "Exit 1" or "Restarting"

**Diagnosis**:
```bash
# Check service status
docker compose ps

# View logs
docker compose logs backend

# Check for specific errors
docker compose logs backend | grep -i error
```

**Common causes and solutions**:

1. **Port already in use**:
   ```bash
   # Find what's using the port
   sudo lsof -i :8000

   # Kill the process or change port in docker-compose.yml
   ```

2. **Missing dependencies**:
   ```bash
   # First try: install inside the running container (fast)
   docker compose exec backend pip install -r requirements.txt
   docker compose exec frontend npm install

   # Only if the above fails (e.g., system package missing): rebuild
   docker compose build --no-cache backend
   docker compose up -d backend
   ```

3. **Database not ready**:
   ```bash
   # Check database health
   docker compose ps postgres

   # Wait for healthy status, then restart backend
   docker compose restart backend
   ```

4. **Configuration error**:
   ```bash
   # Check environment variables
   docker compose exec backend env | grep DATABASE_URL

   # Verify .env file exists and is correct
   cat .env
   ```

---

### Cannot Connect to Database/Redis/OpenSearch

**Symptoms**:
- Connection refused errors
- Timeout errors
- "Service not available" errors

**Diagnosis**:
```bash
# Check all services are running
docker compose ps

# Check specific service health
docker compose logs postgres | tail -20
docker compose logs redis | tail -20
docker compose logs opensearch | tail -20
```

**Solutions**:

1. **Service not healthy yet**:
   ```bash
   # Wait for services to be ready
   docker compose ps
   # Look for "healthy" status

   # Or check manually
   docker compose exec postgres pg_isready -U user
   docker compose exec redis redis-cli ping
   curl http://localhost:9200/_cluster/health
   ```

2. **Wrong connection string**:
   ```bash
   # Check environment variables
   docker compose exec backend env | grep DATABASE_URL

   # Should use service name, not localhost:
   # ✅ postgresql://user:pass@postgres:5432/db
   # ❌ postgresql://user:pass@localhost:5432/db
   ```

3. **Network issue**:
   ```bash
   # Restart services
   docker compose restart

   # Or recreate network
   docker compose down
   docker compose up -d
   ```

---

### OpenSearch Won't Start

**Symptoms**:
- OpenSearch container keeps restarting
- "max virtual memory areas vm.max_map_count [65530] is too low" error

**Solution**:
```bash
# Increase vm.max_map_count
sudo sysctl -w vm.max_map_count=262144

# Make permanent
echo "vm.max_map_count=262144" | sudo tee -a /etc/sysctl.conf
```

---

### Out of Memory

**Symptoms**:
- Services crash with "Killed" message
- OOM (Out of Memory) errors in logs

**Solutions**:

1. **Reduce OpenSearch heap**:
   ```yaml
   # docker-compose.yml
   opensearch:
     environment:
       - OPENSEARCH_JAVA_OPTS=-Xms256m -Xmx512m  # Reduced from 512m-512m
   ```

2. **Limit worker concurrency**:
   ```yaml
   # docker-compose.yml
   worker:
     command: celery -A app.celery_app worker --loglevel=info --concurrency=1
     # Reduced from --concurrency=2
   ```

3. **Add swap space** or **increase Docker memory limit**

---

## Test Issues

### Tests Pass Locally But Fail in Container

**Diagnosis**:
```bash
# Compare environments
python --version  # Host
docker compose exec backend python --version  # Container

# Check dependencies
pip list  # Host
docker compose exec backend pip list  # Container
```

**Solutions**:

1. **Different Python versions**: Ensure container uses correct version in Dockerfile

2. **Missing dependencies**: Rebuild container with updated requirements.txt

3. **Environment variables**: Check container has correct env vars
   ```bash
   docker compose exec backend env
   ```

---

### Import Errors

**Symptoms**:
- `ModuleNotFoundError: No module named 'app.api.routes.videos'`
- `ImportError: cannot import name 'function' from 'module'`

**Solutions**:

1. **File doesn't exist**:
   ```bash
   # Verify file exists
   ls backend/app/api/routes/videos.py

   # Check it's in container
   docker compose exec backend ls /app/app/api/routes/videos.py
   ```

2. **Missing `__init__.py`**:
   ```bash
   # Check directory is a package
   ls backend/app/__init__.py
   ls backend/app/api/__init__.py
   ls backend/app/api/routes/__init__.py
   ```

3. **Circular imports**: Refactor to break circular dependency

4. **Path issues**:
   ```bash
   # Check Python path
   docker compose exec backend python -c "import sys; print(sys.path)"
   ```

---

### Database Tests Fail

**Symptoms**:
- "relation does not exist" errors
- "column does not exist" errors
- Data not persisting between tests

**Solutions**:

1. **Migrations not run**:
   ```bash
   docker compose exec backend alembic upgrade head
   ```

2. **Test database not isolated**:
   - Use test fixtures to create clean database
   - Or use pytest-postgresql for test database

3. **Transaction not committed**:
   ```python
   # Ensure commits in test
   db.commit()
   ```

---

## Git and Beads Issues

### Task Not Found

**Symptoms**:
- `bd show <task-id>` says task doesn't exist
- Task visible in main branch but not current branch

**Solution**:
```bash
# Sync beads state from main
bd sync --from-main

# Verify task now exists
bd show <task-id>
```

---

### Beads State Conflicts

**Symptoms**:
- Merge conflict in `.beads/issues.jsonl`
- `bd sync` fails

**Solution**:
```bash
# Manual resolution
vim .beads/issues.jsonl
# Resolve conflict manually

git add .beads/issues.jsonl
git commit -m "Resolve beads sync conflict"

# Or force sync from main (loses local changes)
git checkout main -- .beads/issues.jsonl
git add .beads/issues.jsonl
git commit -m "Force sync beads from main"
```

---

### Cannot Close Task - Blocking Others

**Symptoms**:
- `bd close <task-id>` fails because task blocks other tasks

**Solution**:
```bash
# See what's blocked
bd show <task-id> | grep "Blocks"

# Option 1: Close/remove blocked tasks first
bd close <blocked-task-id>

# Option 2: Remove dependency
bd dep remove <blocked-task-id> <task-id>

# Then close task
bd close <task-id>
```

---

## Performance Issues

### Slow Container Startup

**Causes**:
- Large images
- Many dependencies to download
- Slow model downloads

**Solutions**:

1. **Use image cache**: Don't use `--no-cache` unless necessary

2. **Pre-download models**: Add to Dockerfile
   ```dockerfile
   RUN python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('model-name')"
   ```

3. **Optimize Dockerfile**: Put least-changing layers first
   ```dockerfile
   # Good order:
   COPY requirements.txt .
   RUN pip install -r requirements.txt  # Cached unless requirements change
   COPY . .  # Changes frequently, goes last
   ```

---

### Slow Test Execution

**Causes**:
- Too many integration tests
- Database setup/teardown overhead
- No test parallelization

**Solutions**:

1. **Run only needed tests**:
   ```bash
   # Not this:
   docker compose exec backend pytest tests/

   # This:
   docker compose exec backend pytest tests/unit/test_videos.py -v
   ```

2. **Use test markers**:
   ```python
   @pytest.mark.slow
   def test_full_pipeline():
       pass

   # Skip slow tests
   pytest -m "not slow"
   ```

3. **Parallelize tests** (if pytest-xdist installed):
   ```bash
   docker compose exec backend pytest -n auto
   ```

---

### Slow Hot Reload

**Causes**:
- Large codebase
- Many file watchers
- Volume mount overhead

**Solutions**:

1. **Exclude unnecessary files**:
   ```yaml
   # docker-compose.dev.yml
   services:
     backend:
       volumes:
         - ./backend:/app
         - /app/__pycache__
         - /app/.pytest_cache
         - /app/node_modules
   ```

2. **Use polling if on NFS/network mount**:
   ```yaml
   # docker-compose.dev.yml
   services:
     backend:
       command: uvicorn app.main:app --reload --reload-delay 2
   ```

---

## Common Error Messages

### "Address already in use"

```
Error starting userland proxy: listen tcp4 0.0.0.0:8000: bind: address already in use
```

**Solution**:
```bash
# Find what's using the port
sudo lsof -i :8000

# Kill it
kill -9 <PID>

# Or change port in docker-compose.yml
ports:
  - "8001:8000"  # Changed from 8000:8000
```

---

### "No space left on device"

```
docker: Error response from daemon: no space left on device
```

**Solutions**:
```bash
# Remove unused images
docker image prune -a

# Remove unused volumes
docker volume prune

# Remove unused containers
docker container prune

# Nuclear option - remove everything not currently used
docker system prune -a --volumes
```

---

### "Cannot connect to Docker daemon"

```
ERROR: Cannot connect to the Docker daemon. Is the docker daemon running?
```

**Solutions**:
```bash
# Start Docker daemon
sudo systemctl start docker

# Check Docker status
sudo systemctl status docker

# Add user to docker group (requires logout/login)
sudo usermod -aG docker $USER
```

---

### "Network not found"

```
ERROR: Network <project>_default declared as external, but could not be found
```

**Solution**:
```bash
# Remove references to external network
docker compose down

# Recreate network
docker compose up -d
```

---

## Debugging Strategies

### General Debugging Process

1. **Identify symptoms**: What's not working? What error message?

2. **Check logs**:
   ```bash
   docker compose logs <service> | tail -50
   docker compose logs -f <service>  # Follow in real-time
   ```

3. **Verify environment**:
   ```bash
   docker compose ps  # All services healthy?
   docker compose exec backend env  # Correct env vars?
   ```

4. **Test in isolation**:
   ```bash
   # Can you import the module?
   docker compose exec backend python -c "from app.api.routes import videos"

   # Can you connect to database?
   docker compose exec postgres psql -U user -d db -c "SELECT 1"
   ```

5. **Compare working state**: If it worked before, what changed?
   ```bash
   git log --oneline -10
   git diff HEAD~1  # What changed in last commit?
   ```

---

### Interactive Debugging

**Python debugger**:
```python
# Add to code
import pdb; pdb.set_trace()

# Run tests with output
docker compose exec backend pytest -s tests/unit/test_videos.py
```

**Shell in container**:
```bash
# Get shell access
docker compose exec backend bash

# Now you're inside container
python  # Interactive Python
ls /app  # Explore filesystem
```

---

### Logging

**Add debugging logs**:
```python
import logging

logger = logging.getLogger(__name__)

logger.info(f"Processing video: {video_id}")
logger.debug(f"Video metadata: {metadata}")
logger.error(f"Failed to process: {error}")
```

**View logs**:
```bash
docker compose logs backend | grep "Processing video"
```

---

## When All Else Fails

### Nuclear Option: Full Reset

```bash
# Stop everything
docker compose down

# Remove all containers, images, volumes
docker system prune -a --volumes

# Rebuild from scratch
docker compose -f docker-compose.yml -f docker-compose.dev.yml build --no-cache
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Run migrations
docker compose exec backend alembic upgrade head
```

**Warning**: This deletes all data. Only use if:
- Data is not important
- Nothing else worked

---

### Ask for Help

If you're stuck:

1. **Document what you tried**:
   - What was the goal?
   - What did you try?
   - What were the results?

2. **Gather diagnostic info**:
   ```bash
   docker compose ps > status.txt
   docker compose logs > logs.txt
   env > environment.txt
   ```

3. **Check project-specific documentation**:
   - Is there a troubleshooting section?
   - Are there known issues?

4. **Search for error messages**:
   - Copy exact error message
   - Search GitHub issues, Stack Overflow

---

## Prevention Tips

### Before Starting Work

- [ ] Pull latest code: `git pull`
- [ ] Sync beads: `bd sync --from-main`
- [ ] Start in dev mode: `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d`
- [ ] Check services healthy: `docker compose ps`
- [ ] Run migrations: `docker compose exec backend alembic upgrade head`

### During Work

- [ ] Test frequently (don't wait until the end)
- [ ] Commit incrementally (small, working changes)
- [ ] Check logs if behavior unexpected
- [ ] Restart service if changes not appearing

### Before Closing Task

- [ ] Run all specified tests
- [ ] Check for regressions
- [ ] Review changes: `git diff`
- [ ] Verify beads state: `bd show <task-id>`

---

## Quick Reference

### Most Common Issues

| Symptom | Most Likely Cause | Quick Fix |
|---------|-------------------|-----------|
| Code changes not appearing | Volume mount not active | Restart: `docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d` |
| Tests fail with import error | File not created or missing `__init__.py` | Create file, add `__init__.py` |
| Cannot connect to database | Database not ready | Wait for healthy: `docker compose ps postgres` |
| Tests pass but feature doesn't work | Testing in wrong environment | Test in container: `docker compose exec backend pytest` |
| Task not found | Beads out of sync | Sync: `bd sync --from-main` |
| New package not found | Dependency not installed in container | Install: `docker compose exec backend pip install -r requirements.txt` |
| `npm` not found in frontend | Frontend container missing development stage | Rebuild: `docker compose build frontend` then restart |
| Port already in use | Previous service still running | Kill it: `docker compose down` then start fresh |
| OpenSearch won't start | vm.max_map_count too low | Increase: `sudo sysctl -w vm.max_map_count=262144` |

---

## Diagnostic Commands Cheat Sheet

```bash
# Service status
docker compose ps
docker compose logs <service>
docker compose logs -f <service>

# Container inspection
docker inspect <container>
docker compose exec <service> bash

# Environment
docker compose exec <service> env
docker compose exec <service> python -c "import sys; print(sys.path)"

# Connectivity
docker compose exec backend ping postgres
docker compose exec postgres pg_isready -U user
docker compose exec redis redis-cli ping
curl http://localhost:9200/_cluster/health

# Files
docker compose exec <service> ls /app
docker compose exec <service> cat /app/file.py

# Beads
bd show <task-id>
bd sync --from-main
bd doctor

# Git
git status
git diff
git log --oneline -10
```
