# Agent Loop Setup Guide

This document explains how to initialize and run the agent-based implementation workflow.

## Overview

The workflow uses two types of agents:

1. **Coordinator Agent** - Dispatches tasks to coding agents, monitors completion, handles failures
2. **Coding Agent** - Executes individual tasks (planning or implementation)

Tasks flow through a hierarchy:

```
Phase
  └── Features (created by feature planning task)
        └── "Plan tasks" task (creates implementation tasks)
              └── Implementation tasks (executed sequentially)
                    └── E2E verification task (final task per feature)
  └── Regression Testing feature (final feature, gates phase completion)
```

---

## Prerequisites

### 1. Beads CLI Installed

Verify beads is available:
```bash
bd --version
bd ready
```

### 2. Claude Agent Script

Ensure `run_claude_agent.sh` is executable:
```bash
chmod +x run_claude_agent.sh
```

### 3. Docker Services (for implementation tasks)

```bash
docker compose up -d
# Verify
curl -s http://localhost:8000/api/health
curl -s http://localhost:9200/_cluster/health
```

---

## Step 1: Create the Bootstrap Task

The bootstrap task kicks off the entire workflow. It reads the phase documentation and creates features.

### For Phase 1:

```bash
bd create --title="Plan features for Phase 1" --type=task --priority=1 --description="Read prompt/plan_features.txt for instructions. Then create features and plan tasks for Phase 1.

## Phase Parameters

- **Phase**: phase1
- **Implementation plan**: docs/implementation/phase1.md
- **Test specification**: docs/testing/phase1-test-specification.md
- **Design docs**: docs/design/
- **Regression pack**: docs/testing/regression-pack.md

## Summary

Phase 1 delivers the MVP Core: Upload → Transcribe → Basic Search → Play at Timestamp

User stories covered: V1, V2, V3, P1, P2, P3, S1, S3, M1

## Your Task

1. Read the implementation plan and test specification
2. Identify feature boundaries (expect 4-7 features)
3. Create features with comprehensive descriptions
4. Create a 'Plan tasks' child task for each feature
5. Set up dependencies so features execute sequentially
6. Include Regression Testing as the final feature

See prompt/plan_features.txt for detailed instructions and templates."
```

### Verify Task Created:

```bash
bd ready
# Should show: Plan features for Phase 1
```

---

## Step 2: Run the Coordinator Loop

The coordinator runs continuously, assigning tasks until the phase is complete.

### Option A: Interactive Coordinator (Recommended for First Run)

Run the coordinator as an interactive Claude session:

```bash
claude --prompt "Read prompt/loop_prompt.txt for instructions. Begin the task dispatch loop."
```

The coordinator will:
1. Find ready tasks with `bd ready`
2. Assign each task to a coding agent
3. Wait for completion
4. Check success/failure
5. Handle retries or continue to next task
6. Stop when no tasks remain

### Option B: Single Task Execution

To run just one task manually:

```bash
# Create log directory
mkdir -p logs/run/task_$(date +%s)

# Run coding agent for a specific task
./run_claude_agent.sh \
  --prompt "Read prompt/coding_agent_prompt.txt for standard instructions. Then read the task description (bd show <task-id>) and complete it. Exit after completion." \
  --output-dir logs/run/task_$(date +%s) \
  --model opus
```

---

## Step 3: Monitor Progress

### Check Current State

```bash
# What's ready to work on?
bd ready

# What's in progress?
bd list --status=in_progress

# What's blocked?
bd blocked

# Overall stats
bd stats
```

### Check Feature Progress

```bash
# Show feature and its children
bd show <feature-id>
```

### Check Agent Output

Agent logs are saved to the output directory:
```bash
ls -la logs/run/
tail -f logs/run/<task_dir>/output.log
```

---

## Workflow Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│  Step 1: Bootstrap Task Created                                  │
│  "Plan features for Phase 1"                                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Step 2: Coordinator Assigns Bootstrap Task                      │
│  Agent reads plan_features.txt, creates features                 │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Features Created:                                               │
│  - Feature A (with "Plan tasks for A")                           │
│  - Feature B (with "Plan tasks for B", blocked by A)             │
│  - Feature C (with "Plan tasks for C", blocked by B)             │
│  - Regression Testing (blocked by C)                             │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Coordinator Assigns "Plan tasks for A"                          │
│  Agent reads plan_tasks.txt, creates implementation tasks        │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Tasks Created for Feature A:                                    │
│  - A.1 (blocked by "Plan tasks for A")                           │
│  - A.2 (blocked by A.1)                                          │
│  - A.3 (blocked by A.2)                                          │
│  - A.E2E (blocked by A.3) ← E2E verification                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Coordinator Assigns A.1, A.2, A.3, A.E2E sequentially           │
│  (May reuse agent session if context allows)                     │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Feature A Complete → "Plan tasks for B" unblocked               │
│  Cycle repeats for Feature B, C, etc.                            │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Regression Testing Feature                                      │
│  Agent runs full regression pack from docs/testing/regression-pack.md │
│  All tests must pass to close                                    │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│  Phase 1 Complete                                                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Handling Failures

### Task Left Open (Agent Failed)

The coordinator will:
1. Check `free_space` in agent output
2. If context exhausted → assign fresh agent
3. If other failure → assign fresh agent with extended thinking
4. Retry up to 3 times before stopping

### Task Blocked by New Issue

If an agent discovers a blocker:
1. Agent creates a new blocking task
2. Original task becomes blocked
3. Coordinator assigns the blocking task first
4. After blocker resolved, original task unblocks

### Manual Intervention

If the loop stops unexpectedly:
```bash
# Check what's happening
bd ready
bd list --status=in_progress
bd blocked

# Resume the coordinator
claude --prompt "Read prompt/loop_prompt.txt. Resume the task dispatch loop."
```

---

## Prompt Files Reference

| File | Purpose |
|------|---------|
| `prompt/loop_prompt.txt` | Coordinator instructions |
| `prompt/coding_agent_prompt.txt` | Standard coding agent behavior |
| `prompt/plan_features.txt` | Feature planning instructions |
| `prompt/plan_tasks.txt` | Task planning instructions |

---

## For Future Phases

To start a new phase (e.g., Phase 2):

1. Ensure Phase 1 regression tests pass
2. Create a new bootstrap task:
   ```bash
   bd create --title="Plan features for Phase 2" --type=task --priority=1 --description="Read prompt/plan_features.txt for instructions. Then create features and plan tasks for Phase 2.

   ## Phase Parameters
   - **Phase**: phase2
   - **Implementation plan**: docs/implementation/phase2.md
   - **Test specification**: docs/testing/phase2-test-specification.md
   ..."
   ```
3. Run the coordinator loop
4. Add Phase 2 tests to `docs/testing/regression-pack.md`

---

## Tips

1. **Start small**: Run a single task manually first to verify the setup
2. **Watch the logs**: Monitor agent output for issues
3. **Check git status**: Agents commit incrementally; review changes regularly
4. **Trust but verify**: Spot-check agent work, especially early on
5. **Iterate on prompts**: If agents consistently fail, refine the prompt files
