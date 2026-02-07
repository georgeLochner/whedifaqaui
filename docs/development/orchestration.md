# Development Orchestration

This document explains how autonomous development is orchestrated using a coordinator agent that dispatches tasks to coding agents.

---

## Overview

The development process uses a **two-tier agent architecture**:

```
┌─────────────────────────────────────────────────────────────┐
│                    Coordinator Agent                         │
│  - Monitors task queue (bd ready)                           │
│  - Dispatches tasks to coding agents                        │
│  - Handles failures and retries                             │
│  - Runs continuously until phase complete                   │
└──────────────────────┬──────────────────────────────────────┘
                       │ Spawns & monitors
                       ▼
┌─────────────────────────────────────────────────────────────┐
│                    Coding Agents                             │
│  - Execute individual tasks                                  │
│  - Can be planning agents (create tasks)                    │
│  - Can be implementation agents (write code)                │
│  - Exit after completing assigned task                      │
└─────────────────────────────────────────────────────────────┘
```

---

## Task Hierarchy

Work flows through a hierarchical structure:

```
Phase (e.g., "Phase 1: MVP Core")
  │
  ├── Bootstrap Task: "Plan features for Phase 1"
  │     └── (Creates all features below)
  │
  ├── Feature A: "Video Upload Pipeline"
  │     ├── "Plan tasks for Feature A"  (creates implementation tasks)
  │     ├── Task A.1: "Create upload endpoint"
  │     ├── Task A.2: "Add file validation"
  │     ├── Task A.3: "Implement storage"
  │     └── Task A.E2E: "End-to-end verification"
  │
  ├── Feature B: "Video Transcription" (blocked by Feature A)
  │     ├── "Plan tasks for Feature B"
  │     ├── Task B.1: ...
  │     └── Task B.E2E: ...
  │
  └── Regression Testing Feature (blocked by all others)
        └── "Run full regression pack"
```

---

## Process Flow

### 1. Bootstrap

**Create the bootstrap task** to kick off the phase:

```bash
bd create --title="Plan features for Phase 1" \
          --type=task \
          --priority=1 \
          --description="Read prompt/plan_features.txt for instructions.

## Phase Parameters
- Phase: phase1
- Implementation plan: docs/implementation/phase1.md
- Test specification: docs/testing/phase1-test-specification.md

## Your Task
1. Read implementation plan and test spec
2. Identify feature boundaries (4-7 features)
3. Create features with comprehensive descriptions
4. Create 'Plan tasks' child task for each feature
5. Set up dependencies (sequential execution)
6. Include Regression Testing as final feature"
```

### 2. Feature Planning

**Coordinator assigns bootstrap task** to a planning agent:

The agent:
1. Reads `docs/implementation/phase1.md`
2. Identifies logical feature boundaries
3. Creates feature tasks with dependencies
4. Creates a "Plan tasks" child task for each feature

**Result**: Multiple features in the queue, with dependencies ensuring sequential execution.

### 3. Task Planning

**Coordinator assigns "Plan tasks for Feature A"** to a planning agent:

The agent:
1. Reads feature description
2. Breaks down into atomic implementation tasks (1-3 files each)
3. Creates tasks with dependencies (sequential execution)
4. Adds E2E verification task as final task

**Result**: Implementation tasks ready for coding agents.

### 4. Implementation

**Coordinator assigns implementation tasks** sequentially to coding agents:

Each agent:
1. Reads task description
2. Implements code changes
3. Runs tests
4. Commits changes
5. Closes task
6. Exits

**Result**: Feature implemented incrementally.

### 5. Verification

**Coordinator assigns E2E verification task**:

The agent:
1. Runs end-to-end tests for the feature
2. Verifies all acceptance criteria met
3. Checks for regressions
4. Closes task (and feature)

**Result**: Feature complete and verified.

### 6. Regression Testing

**After all features complete**, coordinator assigns regression testing:

The agent:
1. Runs full regression pack from `docs/testing/regression-pack.md`
2. All tests must pass
3. Closes task

**Result**: Phase complete.

---

## Coordinator Behavior

The coordinator runs continuously in a loop:

```python
while True:
    ready_tasks = bd_ready()

    if not ready_tasks:
        break  # Phase complete

    task = ready_tasks[0]  # Pick first ready task

    success = assign_to_coding_agent(task)

    if success:
        continue  # Next task
    else:
        handle_failure(task)  # Retry or escalate
```

### Task Assignment

```bash
# Coordinator spawns a coding agent
./run_claude_agent.sh \
  --prompt "Read prompt/coding_agent_prompt.txt. Then complete task: bd show <task-id>" \
  --output-dir logs/run/<timestamp>_<task-id> \
  --model opus
```

### Success Detection

Task is successful if:
- Task status changed to `completed`
- Agent exited cleanly
- Logs show no critical errors

### Failure Handling

If task remains `in_progress` after agent exits:

1. **Check context exhaustion**: Look for `free_space` in logs
   - If exhausted → Assign fresh agent (task has handoff notes)

2. **Check error logs**: Look for exceptions/failures
   - Retry with extended thinking budget
   - Retry up to 3 times

3. **Manual escalation**: If 3 retries fail, stop and alert human

---

## Agent Types

### Planning Agents

**Purpose**: Break down work into implementable tasks

**Input**: High-level feature or phase description

**Output**: Multiple granular tasks with dependencies

**Tasks**:
- Bootstrap: "Plan features for Phase X"
- Feature planning: "Plan tasks for Feature Y"

**Prompts**:
- `prompt/plan_features.txt` - For bootstrap tasks
- `prompt/plan_tasks.txt` - For feature task planning

---

### Implementation Agents

**Purpose**: Execute atomic implementation tasks

**Input**: Task description with file specifications

**Output**: Code changes, tests, commit

**Tasks**:
- Any task that modifies code
- E2E verification tasks

**Prompt**: `prompt/coding_agent_prompt.txt`

---

## Dependencies and Blocking

### Sequential Features

```bash
# Feature B can't start until Feature A complete
bd dep add feature-b feature-a
```

This means:
- Feature A "blocks" Feature B
- Feature B is "blocked by" Feature A
- Coordinator won't assign Feature B tasks until Feature A closes

### Sequential Tasks Within Features

```bash
# Task A.2 can't start until A.1 complete
bd dep add task-a2 task-a1
```

### Discovered Blockers

If an agent discovers a dependency during work:

```bash
# Agent creates a blocking task
bd create --title="Fix authentication module" --type=task --priority=1

# Agent blocks current task
bd dep add current-task new-blocking-task

# Current task becomes blocked, coordinator assigns blocker first
```

---

## Monitoring Progress

### Check What's Ready

```bash
bd ready
# Shows tasks with no blockers, ready to work on
```

### Check What's Running

```bash
bd list --status=in_progress
# Shows tasks currently being worked on
```

### Check What's Blocked

```bash
bd blocked
# Shows tasks waiting on dependencies
```

### Check Overall Progress

```bash
bd stats
# Shows open/closed/blocked counts
```

### Check Feature Status

```bash
bd show <feature-id>
# Shows feature and all its child tasks
```

---

## Starting a New Phase

1. **Ensure previous phase complete**:
   ```bash
   bd stats
   # All tasks should be closed
   ```

2. **Verify regression tests pass**:
   ```bash
   docker compose exec backend pytest tests/
   ```

3. **Create bootstrap task** for new phase:
   ```bash
   bd create --title="Plan features for Phase 2" \
             --type=task \
             --priority=1 \
             --description="[See Bootstrap section above]"
   ```

4. **Start coordinator**:
   ```bash
   claude --prompt "Read prompt/loop_prompt.txt. Begin task dispatch loop."
   ```

5. **Update regression pack**:
   - Add Phase 2 tests to `docs/testing/regression-pack.md`

---

## Running the Coordinator

### Interactive Mode (Recommended)

```bash
# Start coordinator as interactive Claude session
claude --prompt "Read prompt/loop_prompt.txt for instructions. Begin the task dispatch loop."
```

The coordinator will:
1. Find ready tasks
2. Assign to coding agents
3. Wait for completion
4. Handle failures
5. Continue until no tasks remain

### Manual Single Task

To test or debug a single task:

```bash
# Create log directory
mkdir -p logs/run/task_$(date +%s)

# Run coding agent directly
./run_claude_agent.sh \
  --prompt "Read prompt/coding_agent_prompt.txt. Then complete: bd show <task-id>" \
  --output-dir logs/run/task_$(date +%s) \
  --model opus
```

---

## Failure Scenarios

### Agent Runs Out of Context

**Symptom**: Task remains `in_progress`, logs show `free_space` low

**Coordinator action**:
1. Read handoff notes in task description
2. Assign fresh agent to continue work

**Agent responsibility**: Add handoff notes before context exhausted (see `prompt/coding_agent_prompt.txt`)

---

### Agent Encounters Bug/Error

**Symptom**: Task remains `in_progress`, logs show errors

**Coordinator action**:
1. Retry with extended thinking budget
2. Up to 3 retries
3. Alert human if all retries fail

---

### Agent Discovers Blocker

**Symptom**: New task created, current task becomes blocked

**Coordinator action**:
1. Assign blocking task first
2. After blocker resolved, original task unblocks
3. Resume original task

---

### Coordinator Stops Unexpectedly

**Manual recovery**:

```bash
# Check current state
bd ready
bd list --status=in_progress
bd blocked

# Resume coordinator
claude --prompt "Read prompt/loop_prompt.txt. Resume task dispatch loop."
```

---

## Log Management

Agent logs are saved to:
```
logs/run/<timestamp>_<task-id>/
  ├── output.log       # Agent output
  ├── verbose.jsonl    # Full session JSON
  └── monitor.log      # Status tracking
```

### Viewing Logs

```bash
# List recent runs
ls -lt logs/run/ | head -10

# Follow current agent output
tail -f logs/run/*/output.log

# Parse agent log for readability
scripts/parse_agent_log.sh logs/run/<task-dir>/verbose.jsonl
```

---

## Prompts Reference

| File | Purpose | Used By |
|------|---------|---------|
| `prompt/loop_prompt.txt` | Coordinator loop instructions | Coordinator agent |
| `prompt/coding_agent_prompt.txt` | Standard coding behavior | Implementation agents |
| `prompt/plan_features.txt` | Feature planning instructions | Bootstrap planning agent |
| `prompt/plan_tasks.txt` | Task planning instructions | Feature planning agents |

---

## Integration with Development Workflow

The orchestration layer sits **above** the development workflow:

```
Orchestration (this document)
  ├── Coordinator dispatches tasks
  ├── Coding agents execute using:
  │     ├── Docker workflow (docker-workflow.md)
  │     ├── Agent protocols (agent-protocols.md)
  │     ├── Task management (task-management.md)
  │     ├── Verification (verification.md)
  │     └── Troubleshooting (troubleshooting.md)
  └── Progress tracked in Beads
```

Individual agents follow the development workflow documentation. The coordinator ensures agents are assigned work in the correct order.

---

## Best Practices

### For Coordinators

- **Monitor don't micromanage**: Let agents complete work autonomously
- **Handle failures gracefully**: Retry before escalating to humans
- **Respect dependencies**: Never assign blocked tasks
- **Log everything**: Detailed logs aid debugging

### For Planning Agents

- **Right-size tasks**: 1-3 files per implementation task
- **Clear descriptions**: Include files to modify, acceptance criteria
- **Sequential dependencies**: Implementation tasks execute in order
- **E2E verification**: Always add final verification task per feature

### For Implementation Agents

- **Follow protocols**: See `agent-protocols.md`
- **Close when done**: Don't leave tasks hanging
- **Add handoffs**: If context limit approaching, add notes
- **Create blockers**: If you discover dependencies, create blocking tasks

---

## Quick Start Summary

1. **Create bootstrap task**: `bd create --title="Plan features for Phase X" ...`
2. **Start coordinator**: `claude --prompt "Read prompt/loop_prompt.txt. Begin."`
3. **Monitor progress**: `bd stats`, `bd ready`, `bd blocked`
4. **Review logs**: `tail -f logs/run/*/output.log`
5. **Wait for completion**: Coordinator stops when no tasks remain

---

## Related Documentation

- [Agent Protocols](agent-protocols.md) - How individual agents work
- [Task Management](task-management.md) - Beads workflow details
- [Docker Workflow](docker-workflow.md) - Development environment
- [Verification](verification.md) - Testing and quality gates
- `prompt/README_setup.md` - Detailed setup guide
