# Task Management with Beads

This document explains how tasks are tracked and managed using the Beads issue tracking system during autonomous agentic development.

---

## Overview

**Beads** is a git-native issue tracker stored in `.beads/issues.jsonl`. It provides:
- Structured task tracking across sessions
- Dependency management (what blocks what)
- Progress visibility for humans and agents
- Persistence in git history

---

## Task Lifecycle

```
pending → in_progress → completed
                     ↘
                      cancelled/wont_fix
```

---

## Common Commands

### Finding Work

```bash
# Show tasks ready to work (no blockers, not closed)
bd ready

# List all open tasks
bd list --status=open

# List tasks in progress
bd list --status=in_progress

# Show all closed tasks
bd list --status=closed
```

### Viewing Task Details

```bash
# Show full task details
bd show <task-id>

# View dependencies
bd show <task-id> | grep -A5 "Blocked by"
bd show <task-id> | grep -A5 "Blocks"
```

### Creating Tasks

```bash
# Create a new task
bd create --title="Implement video upload API" \
          --type=task \
          --priority=2

# Create a bug
bd create --title="Fix video playback on Safari" \
          --type=bug \
          --priority=1

# Create a feature
bd create --title="Add video thumbnail generation" \
          --type=feature \
          --priority=2
```

**Priority levels:**
- `0` or `P0` - Critical (blocking, production down)
- `1` or `P1` - High (important, user-facing)
- `2` or `P2` - Medium (normal priority)
- `3` or `P3` - Low (nice to have)
- `4` or `P4` - Backlog (future consideration)

### Updating Tasks

```bash
# Mark task as in progress
bd update <task-id> --status=in_progress

# Assign to someone
bd update <task-id> --assignee=username

# Update description (for handoffs)
bd update <task-id> --description="[original]

---
Handoff: Completed X. Remaining: Y."
```

### Closing Tasks

```bash
# Close a single task
bd close <task-id>

# Close multiple tasks at once (more efficient)
bd close <task-id1> <task-id2> <task-id3>

# Close with reason
bd close <task-id> --reason="Duplicate of task-123"
```

### Managing Dependencies

```bash
# Add dependency (task-2 depends on task-1)
bd dep add <task-2> <task-1>

# This means:
#   - task-1 BLOCKS task-2
#   - task-2 is BLOCKED BY task-1
#   - task-2 cannot start until task-1 is closed

# View all blocked tasks
bd blocked

# View what blocks a specific task
bd show <task-id> | grep "Blocked by"
```

### Syncing State

```bash
# Pull latest beads state from main branch
bd sync --from-main

# Check sync status
bd sync --status

# Check for issues
bd doctor
```

### Project Statistics

```bash
# View project stats (open/closed/blocked counts)
bd stats
```

---

## Task Structure

Each task in Beads has:

| Field | Description | Example |
|-------|-------------|---------|
| `id` | Unique identifier | `w-6nz.4`, `beads-abc123` |
| `title` | Brief description | "Implement video upload API" |
| `type` | Task category | `task`, `bug`, `feature`, `epic` |
| `status` | Current state | `pending`, `in_progress`, `completed` |
| `priority` | Importance (0-4) | `2` (medium) |
| `assignee` | Who's working on it | `agent-123`, `alice` |
| `description` | Detailed information | Full spec with acceptance criteria |
| `blocks` | Tasks waiting on this | `[beads-xyz]` |
| `blockedBy` | Tasks this waits for | `[beads-abc]` |
| `created` | Creation timestamp | ISO8601 format |
| `updated` | Last modification | ISO8601 format |

---

## Workflows

### Starting a New Task

```bash
# 1. Find available work
bd ready

# Example output:
# w-6nz.5 - Create video upload form component [priority: 2]
# w-6nz.6 - Add video validation logic [priority: 2]

# 2. View task details
bd show w-6nz.5

# 3. Check it's not blocked
bd show w-6nz.5 | grep "Blocked by"

# 4. Claim the task
bd update w-6nz.5 --status=in_progress

# 5. Read the implementation plan
cat docs/implementation/phase1.md  # Find section for w-6nz.5

# 6. Start working...
```

### Completing a Task

```bash
# 1. Verify implementation complete
docker compose exec backend pytest tests/unit/test_videos.py -v

# 2. Commit changes
git add backend/app/api/routes/videos.py
git commit -m "w-6nz.5: Implement video upload API"

# 3. Sync beads state
bd sync --from-main

# 4. Close the task
bd close w-6nz.5

# 5. Find next task
bd ready
```

### Handing Off a Task

```bash
# 1. Commit partial progress
git add <modified-files>
git commit -m "w-6nz.5: Partial - Upload endpoint created (handoff)"

# 2. Update task with handoff note
bd update w-6nz.5 --description="[original description]

---
HANDOFF NOTE ($(date +%Y-%m-%d)):
Completed: Created upload endpoint and validation
Remaining: Add thumbnail generation, error handling
Modified: backend/app/api/routes/videos.py
Next: Implement worker task in celery_app.py
Issues: None
"

# 3. Leave status as in_progress (don't close)

# 4. Exit - next agent will pick it up
```

### Creating Dependent Tasks

```bash
# Create parent task
bd create --title="Implement video processing pipeline" --type=feature

# Note the ID (e.g., w-7a.1)

# Create dependent tasks
bd create --title="Add video upload endpoint" --type=task
# Note ID: w-7a.2

bd create --title="Implement transcoding worker" --type=task
# Note ID: w-7a.3

bd create --title="Add progress tracking API" --type=task
# Note ID: w-7a.4

# Set up dependencies
bd dep add w-7a.3 w-7a.2  # Transcoding depends on upload
bd dep add w-7a.4 w-7a.3  # Progress tracking depends on transcoding

# Verify
bd show w-7a.3
# Should show: "Blocked by: w-7a.2"
```

### Checking Project Progress

```bash
# View statistics
bd stats

# Example output:
# Open tasks: 12
# In progress: 3
# Completed: 45
# Blocked: 2

# See what's blocking progress
bd blocked

# Example output:
# w-7a.3 - Implement transcoding (blocked by w-7a.2)
# w-7a.4 - Add progress tracking (blocked by w-7a.3)
```

---

## Best Practices for Agents

### Task Sizing

**Good task size:**
- Modifies 1-3 files
- Takes 20-50 tool calls to complete
- Has clear acceptance criteria
- Can be verified with tests

**Too large:**
- Modifies 5+ files
- Requires reading 10+ files
- Multiple complex features
- **Solution:** Should be split into smaller tasks

**Too small:**
- Single line change
- No verification needed
- **Solution:** Combine with related work

### Creating Tasks During Development

If you discover new work while implementing:

```bash
# Create a task for the discovery
bd create --title="Add error handling for invalid video formats" \
          --type=task \
          --priority=2

# Add dependency if needed
bd dep add <new-task-id> <current-task-id>

# Continue with current task
# New task will be picked up later
```

### Using Task Descriptions

**Good description:**
```
Create POST /api/videos endpoint for video upload.

Acceptance criteria:
- Accept multipart/form-data with video file
- Validate file type (mp4, mkv, avi)
- Validate file size (max 2GB)
- Store to VIDEO_STORAGE_PATH
- Return video ID and status

Files to modify:
- backend/app/api/routes/videos.py (create)
- backend/tests/unit/test_videos.py (create)

Reference: docs/design/processing-pipeline.md
```

**Bad description:**
```
Add video stuff
```

### Avoiding Duplication

Before creating a new task:

```bash
# Search existing tasks
bd list --status=open | grep -i "video upload"

# Check if similar work exists
bd show <similar-task-id>

# If duplicate, reference instead of creating
bd update <current-task> --description="[original]

See also: <similar-task-id> for related work"
```

---

## Common Scenarios

### Scenario: Task is Blocked

**Symptom:** `bd show <task-id>` shows "Blocked by: [other-task-id]"

**Action:**
1. Check blocking task: `bd show <blocking-task-id>`
2. If blocking task is complete, close it: `bd close <blocking-task-id>`
3. If blocking task is open, work on it first or pick a different task
4. Never start a blocked task (will lack dependencies)

### Scenario: Multiple Agents Working Simultaneously

**Problem:** Two agents might pick the same task

**Prevention:**
1. Agent A: `bd update <task-id> --status=in_progress --assignee=agent-a`
2. Agent B: `bd ready` (won't show tasks already in progress)
3. Agent B: Picks a different task

**If conflict occurs:**
1. Check git history: `git log --oneline --all | grep <task-id>`
2. More recent claim wins
3. Earlier agent should sync and pick new task: `bd sync --from-main && bd ready`

### Scenario: Task Becomes Obsolete

**Symptom:** Requirements changed, task no longer needed

**Action:**
```bash
bd close <task-id> --reason="Obsolete - requirements changed to use X instead"
```

### Scenario: Task is Too Large

**Symptom:** Approaching context limits, task still not complete

**Action:**
1. **Split the remaining work:**
   ```bash
   # Create new tasks for remaining work
   bd create --title="Part 2: Add error handling for upload" --type=task
   bd create --title="Part 3: Add thumbnail generation" --type=task
   ```

2. **Close current task with partial scope:**
   ```bash
   bd update <current-task> --description="[Reduced scope]

   Only implements basic upload endpoint.
   Error handling and thumbnails split to <new-task-1> and <new-task-2>"

   bd close <current-task>
   ```

---

## Integration with Git

### Beads State is Version Controlled

```bash
# Beads state lives in .beads/issues.jsonl
ls .beads/

# It's tracked in git
git status
# Shows: modified: .beads/issues.jsonl

# Commit beads changes with code changes
git add .beads/issues.jsonl
git commit -m "w-6nz.5: Implement video upload + close task"
```

### Syncing Beads on Ephemeral Branches

When working on a feature branch:

```bash
# Pull latest beads state from main
bd sync --from-main

# This fetches main branch's .beads/issues.jsonl
# And merges updates into current branch
```

### Viewing Task History

```bash
# See when task was created/modified
git log --all --oneline -- .beads/issues.jsonl | grep <task-id>

# See task state at specific commit
git show <commit>:.beads/issues.jsonl | grep <task-id>
```

---

## Tips for Efficiency

### Batch Operations

```bash
# Close multiple tasks at once
bd close w-6nz.1 w-6nz.2 w-6nz.3

# More efficient than:
bd close w-6nz.1
bd close w-6nz.2
bd close w-6nz.3
```

### Using Grep for Filtering

```bash
# Find tasks by keyword
bd list --status=open | grep -i "video"

# Find high priority tasks
bd list --status=open | grep "priority: 1"

# Find tasks assigned to you
bd list --status=in_progress | grep "assignee: $(whoami)"
```

### Check Before Starting Work

```bash
# Quick health check
bd doctor

# Issues:
# - Sync problems
# - Orphaned tasks
# - Circular dependencies
```

---

## Troubleshooting

### Error: "Task not found"

```bash
# Sync from main
bd sync --from-main

# Check if task exists
bd list --status=all | grep <task-id>
```

### Error: "Cannot close - tasks blocked by this"

```bash
# See what's blocked
bd show <task-id> | grep "Blocks"

# Either:
# 1. Close or remove dependencies first
# 2. Remove the blocking relationship:
bd dep remove <blocked-task> <this-task>
```

### Beads State Out of Sync

```bash
# Reset to main branch state
bd sync --from-main

# If conflicts, resolve manually
vim .beads/issues.jsonl
git add .beads/issues.jsonl
git commit -m "Resolve beads sync conflict"
```

---

## Summary

**For Agents:**
- `bd ready` - Find available work
- `bd show <task-id>` - Read task details
- `bd update <task-id> --status=in_progress` - Claim task
- Work on task following implementation plan
- `bd close <task-id>` - Mark complete when verified
- `bd sync --from-main` - Keep state current

**For Task Coordination:**
- Use dependencies to enforce build order
- Create appropriately-sized tasks (1-3 files)
- Write clear descriptions with acceptance criteria
- Close tasks promptly when complete
- Hand off with detailed notes if context limit reached

**For Project Management:**
- `bd stats` - Check overall progress
- `bd blocked` - Identify bottlenecks
- `bd list --status=in_progress` - See active work
- Review task descriptions for quality and clarity
