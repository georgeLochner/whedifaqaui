# Central Logging for Claude Agent Runs

This document explains how to use the central logging feature to monitor all agent runs in a single consolidated log file.

## Overview

When running multiple Claude agents via `run_claude_agent.sh`, each creates its own `verbose.jsonl` file in a separate output directory. The central logging feature:

1. **Automatically parses** the verbose JSON logs in real-time
2. **Appends** human-readable output to a central log file
3. **Consolidates** all agent runs in one place for easy monitoring
4. **Runs in background** without affecting agent performance

## Quick Start

### Basic Usage

Add the `--central-log` option when running an agent:

```bash
./run_claude_agent.sh \
  --prompt "Your task here" \
  --output-dir logs/run/1234 \
  --central-log logs/agent.log
```

### Watch the Central Log

In another terminal, watch all agent activity in real-time:

```bash
tail -f logs/agent.log
```

### Multiple Agents

All agents writing to the same central log will be consolidated:

```bash
# Terminal 1: Start first agent
./run_claude_agent.sh \
  --prompt "Task 1" \
  --output-dir logs/run/001 \
  --central-log logs/agent.log

# Terminal 2: Start second agent
./run_claude_agent.sh \
  --prompt "Task 2" \
  --output-dir logs/run/002 \
  --central-log logs/agent.log

# Terminal 3: Watch both
tail -f logs/agent.log
```

## How It Works

### Components

1. **`run_claude_agent.sh`** - Main wrapper script
   - Spawns the Claude agent
   - Optionally starts background logger
   - Manages cleanup

2. **`logger_background.sh`** - Background logger
   - Parses `verbose.jsonl` in real-time
   - Extracts key information
   - Appends to central log file
   - Automatically exits when agent completes

3. **Central log file** (e.g., `logs/agent.log`)
   - Single consolidated log for all runs
   - Human-readable format
   - Organized by run with clear separators

### Log Format

Each agent run in the central log is formatted as:

```
═══════════════════════════════════════════════════════════════════
RUN: 1234567890_task-id | Started: 2026-02-07 14:30:15
Log: logs/run/1234567890_task-id/verbose.jsonl
═══════════════════════════════════════════════════════════════════

[14:30:15] System initialized (model: claude-opus-4-6)
[14:30:16] Hook completed: SessionStart:startup

[14:30:17] Claude Message #1:
I'll start by reading the task description...

[14:30:17] Tool #1: Read
  Reading: /path/to/file.txt
  ✓ Success

[14:30:18] Tool #2: Bash
  $ docker compose exec backend pytest tests/
  ✓ Success

───────────────────────────────────────────────────────────────────
Run completed: 2026-02-07 14:35:22
Messages: 5 | Tool calls: 12
═══════════════════════════════════════════════════════════════════
```

## Configuration

### Default Central Log Location

By default, there is no central log. You must specify `--central-log` explicitly.

Recommended location:
```bash
--central-log logs/agent.log
```

### Run ID

The run ID is automatically extracted from the output directory name:
- `logs/run/1234_task-name` → Run ID: `1234_task-name`
- This appears in the central log header for easy identification

## Viewing Options

### Real-time Monitoring

Watch live as agents run:
```bash
tail -f logs/agent.log
```

### Search for Specific Runs

Find activity for a specific run:
```bash
grep "RUN: 1234" logs/agent.log -A 50
```

### Filter by Tool

See all Bash commands across all runs:
```bash
grep "Tool.*: Bash" logs/agent.log -A 1
```

### Count Messages/Tools

Count total tool calls:
```bash
grep "Tool #" logs/agent.log | wc -l
```

Count Claude messages:
```bash
grep "Claude Message" logs/agent.log | wc -l
```

## Advanced Usage

### Custom Log Location

You can specify any path for the central log:
```bash
--central-log /var/log/claude/all_agents.log
```

### Per-Day Logs

Automatically create daily log files:
```bash
DAILY_LOG="logs/agent_$(date +%Y-%m-%d).log"
./run_claude_agent.sh \
  --prompt "Task" \
  --output-dir logs/run/001 \
  --central-log "$DAILY_LOG"
```

### Per-Feature Logs

Organize logs by feature:
```bash
# Feature A agents
./run_claude_agent.sh \
  --prompt "Feature A task" \
  --output-dir logs/run/A001 \
  --central-log logs/feature_a.log

# Feature B agents
./run_claude_agent.sh \
  --prompt "Feature B task" \
  --output-dir logs/run/B001 \
  --central-log logs/feature_b.log
```

### Disable Central Logging

Simply omit the `--central-log` option:
```bash
./run_claude_agent.sh \
  --prompt "Task" \
  --output-dir logs/run/001
# No central logging
```

## Troubleshooting

### Logger Not Starting

**Symptom:** No output in central log

**Check:**
1. Verify `logger_background.sh` exists and is executable:
   ```bash
   ls -l logger_background.sh
   chmod +x logger_background.sh
   ```

2. Check monitor.log for errors:
   ```bash
   cat logs/run/*/monitor.log | grep logger
   ```

### Central Log Not Updating

**Symptom:** Central log stops updating mid-run

**Check:**
1. Verify logger process is running:
   ```bash
   cat logs/run/*/logger.pid
   ps aux | grep logger_background
   ```

2. Check for logger process crash:
   ```bash
   # Logger should exit when agent completes
   # If agent is running but logger isn't, restart it manually:
   ./logger_background.sh \
     logs/run/1234/verbose.jsonl \
     logs/agent.log \
     1234 &
   ```

### JSON Parsing Errors

**Symptom:** Incomplete or missing entries in central log

**Solution:**
- The logger automatically skips invalid JSON lines
- Check the original `verbose.jsonl` for corruption
- The interactive monitoring scripts (`parse_agent_log.sh`, `parse_agent_log_detailed.sh`) can help debug

### Central Log Growing Too Large

**Solution:**
1. Use daily logs:
   ```bash
   --central-log logs/agent_$(date +%Y-%m-%d).log
   ```

2. Archive old logs:
   ```bash
   gzip logs/agent_2026-01-*.log
   ```

3. Use logrotate for automatic management

## Comparison with Interactive Monitors

### Central Logging (`--central-log`)

**Best for:**
- Running multiple agents
- Long-term record keeping
- Background monitoring
- Searching across all runs

**Features:**
- Automatic background operation
- Consolidated multi-run view
- Persistent log file
- No interaction needed

### Interactive Monitors (`parse_agent_log.sh`, `parse_agent_log_detailed.sh`)

**Best for:**
- Debugging a single agent run
- Detailed real-time inspection
- Filtering specific event types
- Color-coded terminal output

**Features:**
- Full color output
- Filtering options
- Statistics tracking
- Manual control

**When to use both:**
- Use `--central-log` for automatic consolidated logging
- Use interactive monitors when debugging specific runs

## Example Workflows

### Development Workflow

```bash
# Start agent with central logging
./run_claude_agent.sh \
  --prompt "$(cat prompt/task_prompt.txt)" \
  --output-dir logs/run/$(date +%s)_dev-test \
  --central-log logs/agent.log \
  --model opus

# In another terminal, watch progress
tail -f logs/agent.log

# If something looks wrong, open detailed monitor on specific run
cd logs/run/1234567890_dev-test
../../parse_agent_log_detailed.sh --tools-only verbose.jsonl
```

### Production/CI Workflow

```bash
#!/bin/bash
# run_all_tasks.sh

CENTRAL_LOG="logs/agent_$(date +%Y-%m-%d_%H-%M-%S).log"

for task_id in task1 task2 task3; do
  echo "Starting $task_id..."
  ./run_claude_agent.sh \
    --prompt "$(cat prompts/${task_id}.txt)" \
    --output-dir "logs/run/$(date +%s)_${task_id}" \
    --central-log "$CENTRAL_LOG" \
    --model sonnet \
    --idle-timeout 120

  echo "$task_id complete"
done

echo "All tasks complete. View log: $CENTRAL_LOG"
```

### Debugging Workflow

```bash
# Run with central log
./run_claude_agent.sh \
  --prompt "Debug task X" \
  --output-dir logs/run/debug_001 \
  --central-log logs/debug.log

# Watch central log
tail -f logs/debug.log

# If errors appear, use detailed monitor for specific run
cd logs/run/debug_001
../../parse_agent_log_detailed.sh --full verbose.jsonl > detailed_debug.txt
```

## Performance Impact

The background logger:
- **Minimal CPU usage** - only parses new lines as they appear
- **No disk I/O impact** - writes are buffered and asynchronous
- **No agent delay** - runs independently in separate process
- **Automatic cleanup** - exits when agent completes

## Files and Locations

```
project/
├── run_claude_agent.sh           # Main wrapper (modified)
├── logger_background.sh          # Background logger (new)
├── logs/
│   ├── agent.log                 # Central log (consolidated)
│   └── run/
│       ├── 1234_task-a/
│       │   ├── verbose.jsonl     # Raw JSON log
│       │   ├── result.txt        # Agent result
│       │   ├── monitor.log       # Monitor log
│       │   └── logger.pid        # Logger PID (temporary)
│       └── 5678_task-b/
│           └── ...
└── scripts/parse_agent_log*.sh   # Post-mortem log parsers
```

## Summary

The central logging feature provides:
- ✅ **Single consolidated view** of all agent runs
- ✅ **Automatic background operation** with no manual intervention
- ✅ **Human-readable format** instead of raw JSON
- ✅ **Real-time updates** as agents run
- ✅ **Easy searching** across all historical runs
- ✅ **Zero impact** on agent performance

Enable it by adding `--central-log logs/agent.log` to your `run_claude_agent.sh` commands.
