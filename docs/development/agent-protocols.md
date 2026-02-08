# Agent Development Protocols

This document defines how autonomous coding agents should work within the Docker-based development environment to execute implementation tasks.

---

## Core Principles

1. **Read Before Writing** - Always read implementation plans and design docs before starting
2. **Develop in Docker Dev Mode** - Use volume-mapped containers for fast iteration
3. **Verify Before Closing** - Run tests and verify functionality before marking tasks complete
4. **Commit Incrementally** - Small, logical commits with clear messages
5. **Document Handoffs** - If context limit reached, document progress for next agent

---

## Standard Workflow

### 1. Task Initialization

**Before writing any code:**

```bash
# Read the task details
bd show <task-id>

# Check if task is blocked by dependencies
bd show <task-id> | grep -A5 "Blocked by"

# Mark task as in progress
bd update <task-id> --status=in_progress

# Read the implementation plan
cat docs/implementation/phase<N>.md  # Find the relevant section

# Read relevant design docs (referenced in implementation plan)
cat docs/design/<relevant-doc>.md
```

**Checklist**:
- [ ] Task is not blocked by dependencies
- [ ] Implementation plan read and understood
- [ ] Design docs reviewed
- [ ] Task marked as `in_progress`

---

### 2. Environment Setup

**Start services in development mode:**

```bash
# Start all services with volume mounts and hot reload
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Verify all services are healthy
docker compose ps

# Check for errors in logs
docker compose logs --tail=50
```

**If services are already running, verify mode:**

```bash
# Check if volume mounts are active
docker compose ps | grep -i "volumes"

# Or inspect a specific service
docker inspect <project>_backend_1 | grep -A10 "Mounts"
```

**If wrong mode detected, restart:**

```bash
docker compose down
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

---

### 3. Code Development

**Edit code on the host filesystem:**

```bash
# ✅ CORRECT: Edit on host
vim ./backend/app/api/routes/videos.py
# or use Read/Edit/Write tools

# ❌ WRONG: Don't edit inside container
docker compose exec backend vim /app/app/api/routes/videos.py
```

**Why?**
- Host edits persist and are version controlled
- Volume mounts make changes immediately visible in container
- Hot reload automatically picks up changes

**Development cycle:**

1. **Edit code** on host using Read/Edit/Write tools
2. **Changes reflect automatically** (if hot reload enabled)
3. **Test immediately** without rebuild
4. **Iterate quickly** based on test results

---

### 4. Testing and Verification

**Run tests inside the container environment:**

```bash
# Run unit tests
docker compose exec backend pytest tests/unit/test_videos.py -v

# Run integration tests
docker compose exec backend pytest tests/integration/ -v

# Run specific test function
docker compose exec backend pytest tests/unit/test_videos.py::test_upload -v

# Manual verification (if no tests exist)
docker compose exec backend python -c "from app.api.routes import videos; print(dir(videos))"
```

**Verification loop:**

```
┌─────────────────────────────────────────────────────────────┐
│ 1. Implement feature                                         │
│    ↓                                                         │
│ 2. Run tests                                                 │
│    ↓                                                         │
│    ├─→ Tests PASS → Verify no regressions → Continue        │
│    │                                                         │
│    └─→ Tests FAIL → Read error → Fix issue → Rerun tests    │
│                       ↑                            │         │
│                       └────────────────────────────┘         │
└─────────────────────────────────────────────────────────────┘
```

**Never close a task with failing tests.**

---

### 5. Commit Changes

**When tests pass and functionality is verified:**

```bash
# Check what changed
git status
git diff

# Stage specific files (avoid staging unrelated changes)
git add backend/app/api/routes/videos.py
git add backend/tests/unit/test_videos.py

# Commit with descriptive message
git commit -m "$(cat <<'EOF'
<task-id>: Add video upload endpoint

Implement POST /api/videos endpoint with multipart file upload,
validation, and storage. Includes unit tests for validation logic.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
EOF
)"
```

**Commit message format:**
```
<task-id>: <Brief summary>

<Detailed description of changes>
<Why these changes were made>
<Any important notes for future developers>

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>
```

**Commit frequently:**
- After each logical unit of work
- When a specific test starts passing
- When a subtask within the larger task is complete

---

### 6. Task Completion

**Close the task when fully verified:**

```bash
# Sync beads state from main (if on ephemeral branch)
bd sync --from-main

# Close the task
bd close <task-id>

# Verify it's closed
bd show <task-id>
```

**Only close when:**
- [ ] All specified tests pass
- [ ] No regressions in related tests
- [ ] Manual verification complete (if applicable)
- [ ] Code is committed
- [ ] Documentation updated (if needed)

---

### 7. Context Limit Handoff

**If you cannot finish the task due to context limits:**

```bash
# Add handoff note to the task
bd update <task-id> --description="[original description]

---
HANDOFF NOTE:
Completed: Created video upload endpoint and basic validation
Remaining: Add thumbnail generation and error handling
Modified files: backend/app/api/routes/videos.py
Next steps: Implement thumbnail worker task in celery_app.py

Issues encountered: None
"

# Commit partial progress
git add <modified-files>
git commit -m "<task-id>: Partial - Add video upload endpoint (handoff)"

# Leave task open (in_progress status)
# The next agent will pick it up and continue
```

**Handoff checklist:**
- [ ] Description updated with handoff note
- [ ] Partial progress committed
- [ ] Clear "next steps" documented
- [ ] Task left in `in_progress` status
- [ ] Modified files listed

---

## Common Scenarios

### Scenario 1: Tests Fail After Implementation

**Symptom**: Test errors after implementing feature

**Protocol**:

1. **Read the test failure carefully**:
   ```bash
   docker compose exec backend pytest tests/unit/test_videos.py -v
   ```

2. **Understand what's expected vs actual**:
   - What did the test expect?
   - What did your code actually do?
   - Where is the mismatch?

3. **Fix the issue** (don't modify the test unless it's clearly wrong):
   ```bash
   vim ./backend/app/api/routes/videos.py
   ```

4. **Rerun tests**:
   ```bash
   docker compose exec backend pytest tests/unit/test_videos.py -v
   ```

5. **Repeat until all tests pass**

**Never:**
- ❌ Modify tests to make them pass (unless test is incorrect)
- ❌ Skip failing tests
- ❌ Close task with failing tests

---

### Scenario 2: Code Changes Not Appearing

**Symptom**: Edited code but container still uses old behavior

**Protocol**:

1. **Verify you're in dev mode**:
   ```bash
   docker compose ps
   ```

2. **Check what code is in the container**:
   ```bash
   docker compose exec backend cat /app/app/api/routes/videos.py
   ```

3. **If code is old**, restart in dev mode:
   ```bash
   docker compose down
   docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d
   ```

4. **If still old**, volume mount may not be active:
   - Restart with dev compose file (see docker-workflow.md)

---

### Scenario 3: Multiple Files Need Modification

**Symptom**: Task requires changes to 5+ files

**Protocol**:

1. **Check if task is properly scoped**:
   - Implementation plans should have 1-3 files per task
   - If task is too large, it should be split

2. **Make changes incrementally**:
   - Change 1-2 files at a time
   - Test after each change
   - Commit when working

3. **If context limit approaching**:
   - Commit current progress
   - Add handoff note
   - Leave task open for next agent

**Don't:**
- ❌ Change all files at once without testing
- ❌ Make untested commits "just to save progress"

---

### Scenario 4: Task Requires a New Dependency

**Symptom**: Implementation needs a package not yet in requirements.txt or package.json

**Protocol**:

1. **Edit the manifest file on host**:
   ```bash
   # Add the package to requirements.txt or package.json
   # Use Read/Edit tools as normal
   ```

2. **Install inside the running container** (do NOT rebuild):
   ```bash
   # Backend
   docker compose exec backend pip install -r requirements.txt

   # Frontend
   docker compose exec frontend npm install
   ```

3. **Verify the package is available**:
   ```bash
   docker compose exec backend python -c "import new_package"
   docker compose exec frontend node -e "require('new-package')"
   ```

4. **Commit the manifest file** along with your code changes

**Never:**
- ❌ Run `docker compose build` just to add a dependency
- ❌ Install packages without updating the manifest file (lost on next build)
- ❌ Run `npm install` or `pip install` on the host — always inside the container

---

### Scenario 5: No Tests Exist for Task

**Symptom**: Implementation plan doesn't specify tests

**Protocol**:

1. **Check test specifications**:
   ```bash
   cat docs/testing/phase<N>-test-specification.md
   ```

2. **If tests should exist but don't**:
   - Create basic tests first
   - Then implement feature
   - Then verify tests pass

3. **If no tests specified, verify manually**:
   ```bash
   # For API endpoints:
   curl -X POST http://localhost:8000/api/videos

   # For Python functions:
   docker compose exec backend python -c "from app.api.routes.videos import upload; print(upload)"

   # For database migrations:
   docker compose exec backend alembic upgrade head
   docker compose exec backend psql -U user -d db -c "\\dt"
   ```

4. **Document what you tested** in commit message

---

## Anti-Patterns to Avoid

### ❌ Don't: Edit Files Inside Containers

```bash
# WRONG
docker compose exec backend vim /app/app/api/routes/videos.py
```

**Why?** Changes inside container are lost when container restarts.

**Instead:** Edit on host filesystem using Read/Edit/Write tools.

---

### ❌ Don't: Commit Without Testing

```bash
# WRONG
git add .
git commit -m "Implement feature X"
# (never ran tests)
```

**Why?** Untested code often breaks in unexpected ways.

**Instead:** Always run tests before committing.

---

### ❌ Don't: Close Tasks With Failing Tests

```bash
# WRONG
$ docker compose exec backend pytest
# ... 2 tests failed ...
$ bd close <task-id>  # WRONG!
```

**Why?** Failing tests indicate incomplete or broken implementation.

**Instead:** Fix issues until all tests pass, then close.

---

### ❌ Don't: Skip Reading Implementation Plans

```bash
# WRONG
bd update <task-id> --status=in_progress
# ... start writing code without reading plan ...
```

**Why?** Implementation plans contain critical context, design decisions, and acceptance criteria.

**Instead:** Always read implementation plan and design docs first.

---

### ❌ Don't: Rebuild to Install Dependencies

```bash
# WRONG
vim backend/requirements.txt        # Add new package
docker compose build backend        # Slow full rebuild (~minutes)
docker compose up -d backend        # Restart with new image
```

**Why?** Rebuilding the entire image to add one package wastes minutes when it can be done in seconds.

**Instead:** Install inside the running container:
```bash
vim backend/requirements.txt                                    # Add new package
docker compose exec backend pip install -r requirements.txt     # Fast (~seconds)
```

The Dockerfile will pick up the updated manifest on the next build (recovery or fresh setup).

---

### ❌ Don't: Change Docker Image Versions

```yaml
# WRONG - Changed minor version
opensearch:
  image: opensearchproject/opensearch:2.12.0  # Changed from 2.11.1

# WRONG - Using floating tags
postgres:
  image: postgres:16-alpine  # Should be 16.1-alpine
```

**Why?**
- Forces large image downloads for all developers
- Can introduce breaking changes mid-development
- Breaks reproducibility

**Versions are frozen** in `docs/design/technology-stack.md` (see "Docker Images" section). Never change Docker image versions unless explicitly tasked to do so.

**If you need a newer version:** Create a task to evaluate, test, and update across all documentation.

---

## Decision Trees

### Should I Rebuild the Docker Image?

```
What type of change did you make?
  │
  ├─ Source code (.py, .tsx, .ts, .css, etc.)
  │   └─ ❌ No rebuild needed
  │       Code is volume-mapped; hot reload picks up changes automatically.
  │
  ├─ Dependencies (requirements.txt, package.json)
  │   └─ ❌ No rebuild needed — install inside the running container:
  │       • Backend:  docker compose exec backend pip install -r requirements.txt
  │       • Frontend: docker compose exec frontend npm install
  │       The Dockerfile will pick these up on the next build automatically.
  │
  └─ Dockerfile, system packages, or base image
      └─ ✅ Rebuild required:
          docker compose build <service>
          docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d <service>
```

---

### Should I Close This Task?

```
Are all specified tests passing?
  ├─ NO → ❌ Don't close
  │        ├─ Fix failing tests
  │        └─ Re-run until passing
  │
  └─ YES → Are there regressions in related tests?
            ├─ YES → ❌ Don't close
            │         └─ Fix regressions
            │
            └─ NO → Is code committed?
                     ├─ NO → ❌ Don't close
                     │        └─ Commit changes first
                     │
                     └─ YES → ✅ Safe to close
                               bd close <task-id>
```

---

### Should I Hand Off This Task?

```
Have I read 10+ files or performed 15+ tool calls?
  ├─ NO → ⏭️ Continue working
  │
  └─ YES → Is the task complete?
            ├─ YES → ✅ Close normally
            │         (context limits don't matter)
            │
            └─ NO → Can I finish in next 5-10 actions?
                     ├─ YES → ⏭️ Push to complete
                     │
                     └─ NO → ✅ Hand off
                              ├─ Commit progress
                              ├─ Update task with handoff note
                              └─ Leave task open
```

---

## Tools and Commands Reference

### Task Management (Beads)

```bash
bd show <task-id>                          # View task details
bd update <task-id> --status=in_progress   # Claim task
bd close <task-id>                         # Mark complete
bd sync --from-main                        # Sync beads state
```

### Docker Management

```bash
# Start dev mode
docker compose -f docker-compose.yml -f docker-compose.dev.yml up -d

# Stop services
docker compose down

# Restart service
docker compose restart <service>

# View logs
docker compose logs -f <service>

# Check status
docker compose ps

# Execute command in container
docker compose exec <service> <command>
```

### Testing

```bash
# Run all tests
docker compose exec backend pytest -v

# Run specific test file
docker compose exec backend pytest tests/unit/test_videos.py -v

# Run specific test function
docker compose exec backend pytest tests/unit/test_videos.py::test_upload -v

# Run with output capture disabled (see print statements)
docker compose exec backend pytest -s

# Run with coverage
docker compose exec backend pytest --cov=app tests/
```

### Git

```bash
git status                    # Check what changed
git diff                      # See changes
git add <files>               # Stage changes
git commit -m "..."           # Commit with message
git log --oneline -5          # Recent commits
```

---

## Summary Checklist

Before starting any task:
- [ ] Read implementation plan
- [ ] Read relevant design docs
- [ ] Start services in dev mode
- [ ] Mark task as in_progress

While working:
- [ ] Edit code on host (not in container)
- [ ] Test frequently
- [ ] Commit incrementally

Before closing:
- [ ] All tests pass
- [ ] No regressions
- [ ] Code committed
- [ ] Close task with `bd close <task-id>`

If context limit reached:
- [ ] Commit progress
- [ ] Update task with handoff note
- [ ] Leave task open

**Default mode**: Development with volume mounts.
**Default verification**: Run tests before closing.
**Default commit frequency**: After each logical unit of work.
