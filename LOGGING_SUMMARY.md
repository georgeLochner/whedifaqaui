# Agent Logging System - Complete Summary

This document summarizes the complete logging system for Claude agent runs.

---

## 📁 File Structure

```
whedifaqaui/
├── run_claude_agent.sh              ← Main wrapper (MODIFIED: added --central-log)
├── logger_background.sh             ← NEW: Background logger for central log
├── CENTRAL_LOGGING.md               ← NEW: Central logging documentation
├── LOGGING_SUMMARY.md               ← NEW: This file
├── test_orphan_cleanup.sh           ← NEW: Test script for cleanup verification
├── example_central_logging.sh       ← NEW: Example usage
├── logs/
│   ├── agent.log                    ← NEW: Central consolidated log
│   └── run/
│       └── <timestamp>_<task-id>/
│           ├── verbose.jsonl        ← Raw JSON log (unchanged)
│           ├── result.txt           ← Final result (unchanged)
│           ├── monitor.log          ← Activity monitor (unchanged)
│           ├── agent.pid            ← Temp PID file (unchanged)
│           └── logger.pid           ← Temp logger PID (NEW, if --central-log used)
└── scripts/
    ├── parse_agent_log.sh             ← MODIFIED: Now a log parser (not real-time)
    ├── parse_agent_log_detailed.sh    ← MODIFIED: Now a log parser (not real-time)
    └── PARSER_README.md            ← UPDATED: Reflects new parser behavior
```

---

## 🎯 Three Use Cases

### 1. Real-time Monitoring (NEW)

**When:** You want to watch all agent runs in one place as they happen

**How:**
```bash
# Start agents with central logging
./run_claude_agent.sh \
  --prompt "Task 1" \
  --output-dir logs/run/001 \
  --central-log logs/agent.log

# Watch in real-time
tail -f logs/agent.log
```

**What happens:**
- `logger_background.sh` spawns automatically
- Parses `verbose.jsonl` as the agent runs
- Appends human-readable output to `logs/agent.log`
- Multiple agents append to the same central log
- Automatically cleans up when agent completes

**Documentation:** `CENTRAL_LOGGING.md`

---

### 2. Post-Mortem Analysis

**When:** Agent completed, you want to analyze what happened

**How:**
```bash
# Quick overview
./scripts/parse_agent_log.sh logs/run/001/verbose.jsonl

# Detailed analysis
./scripts/parse_agent_log_detailed.sh logs/run/001/verbose.jsonl

# Focus on specific aspects
./scripts/parse_agent_log_detailed.sh --tools-only logs/run/001/verbose.jsonl
./scripts/parse_agent_log_detailed.sh --messages-only logs/run/001/verbose.jsonl
```

**What happens:**
- Scripts parse the completed `verbose.jsonl` file
- Display human-readable output
- Show statistics (message count, tool calls, errors)
- Exit immediately (no watching/following)

**Documentation:** `scripts/PARSER_README.md`

---

### 3. Raw Log Inspection

**When:** You need the exact JSON for debugging or tooling

**How:**
```bash
# View raw JSON log
cat logs/run/001/verbose.jsonl

# Parse specific fields with jq
jq 'select(.type=="assistant")' logs/run/001/verbose.jsonl

# Search for errors
jq 'select(.tool_use_result.is_error==true)' logs/run/001/verbose.jsonl
```

**What you get:**
- Complete JSON stream from Claude CLI
- All metadata preserved
- Can be processed with any JSON tool

---

## 🔄 Complete Workflow Example

```bash
# 1. Start agent with central logging
./run_claude_agent.sh \
  --prompt "Implement feature X" \
  --output-dir logs/run/$(date +%s)_feature-x \
  --central-log logs/agent.log \
  --model opus

# 2. Monitor in real-time (in another terminal)
tail -f logs/agent.log

# 3. After completion, analyze details
RUN_DIR=$(ls -t logs/run/ | head -1)
./scripts/parse_agent_log_detailed.sh --tools-only logs/run/$RUN_DIR/verbose.jsonl

# 4. Check specific tool calls
./scripts/parse_agent_log_detailed.sh logs/run/$RUN_DIR/verbose.jsonl | grep "Bash"

# 5. Export analysis for documentation
./scripts/parse_agent_log_detailed.sh --no-color --full \
  logs/run/$RUN_DIR/verbose.jsonl > analysis.txt
```

---

## 📊 Comparison Matrix

| Feature | Central Log | Parser Scripts | Raw JSON |
|---------|-------------|----------------|----------|
| **Real-time monitoring** | ✅ Yes (tail -f) | ❌ No | ❌ No |
| **Multi-run consolidation** | ✅ Yes | ❌ No (one at a time) | ❌ No |
| **Automatic (no manual action)** | ✅ Yes (with --central-log) | ❌ Manual | ❌ Manual |
| **Human-readable** | ✅ Yes | ✅ Yes | ❌ No (JSON) |
| **Filtering options** | ❌ No | ✅ Yes (--tools-only, etc) | ✅ Yes (jq) |
| **Statistics** | ❌ No | ✅ Yes (detailed script) | ❌ No |
| **Complete data** | ❌ Truncated | ❌ Truncated (--full for more) | ✅ Yes |
| **Searchable** | ✅ Yes (grep) | ✅ Yes (grep) | ✅ Yes (jq) |
| **For debugging** | ⚠️ Quick overview | ✅ Best choice | ✅ Deep dive |

---

## 🚀 Quick Reference

### Enable Central Logging
```bash
./run_claude_agent.sh --prompt "..." --output-dir DIR --central-log logs/agent.log
```

### Watch Central Log
```bash
tail -f logs/agent.log
```

### Parse Completed Log (Simple)
```bash
./scripts/parse_agent_log.sh logs/run/DIR/verbose.jsonl
```

### Parse Completed Log (Detailed)
```bash
./scripts/parse_agent_log_detailed.sh [--full] [--tools-only] [--messages-only] logs/run/DIR/verbose.jsonl
```

### Search All Runs
```bash
grep "ERROR" logs/agent.log
grep "RUN: task-id" logs/agent.log -A 50
```

### Count Statistics
```bash
# Total tool calls across all runs
grep "Tool #" logs/agent.log | wc -l

# Tool calls in specific run
./scripts/parse_agent_log_detailed.sh --tools-only logs/run/DIR/verbose.jsonl | grep "TOOL #" | wc -l
```

---

## ⚙️ What Changed

### New Files
1. **`logger_background.sh`** - Background process that parses verbose.jsonl and appends to central log
2. **`CENTRAL_LOGGING.md`** - Complete documentation for central logging feature
3. **`test_orphan_cleanup.sh`** - Test script to verify no orphan processes left behind
4. **`example_central_logging.sh`** - Demo script showing usage
5. **`LOGGING_SUMMARY.md`** - This file

### Modified Files
1. **`run_claude_agent.sh`** - Added `--central-log` option and logger spawning
2. **`scripts/parse_agent_log.sh`** - Changed from real-time monitor to log parser
3. **`scripts/parse_agent_log_detailed.sh`** - Changed from real-time monitor to log parser
4. **`scripts/PARSER_README.md`** - Updated to reflect parser behavior

### Unchanged Files
- Individual run logs structure (verbose.jsonl, result.txt, monitor.log)
- Raw JSON format and content
- All other functionality of `run_claude_agent.sh`

---

## 🔒 Safety Features

### Orphan Process Prevention
- `logger_background.sh` uses trap handlers to ensure cleanup
- No orphan `tail -f` processes left behind when agent exits
- Test with: `./test_orphan_cleanup.sh`

### Backward Compatibility
- `--central-log` is optional
- Without it, behavior is exactly the same as before
- All existing logs and structure preserved

### Zero Performance Impact
- Logger runs in separate process
- Only parses new lines as they appear
- Buffered async writes to central log

---

## 📚 Documentation Guide

| Document | Purpose |
|----------|---------|
| **LOGGING_SUMMARY.md** (this file) | Overview of entire logging system |
| **CENTRAL_LOGGING.md** | Detailed guide for real-time central logging |
| **scripts/PARSER_README.md** | Guide for post-mortem log parsing scripts |

---

## 💡 Best Practices

1. **Always use central logging for production runs:**
   ```bash
   --central-log logs/agent.log
   ```

2. **Daily rotation for long-running systems:**
   ```bash
   --central-log logs/agent_$(date +%Y-%m-%d).log
   ```

3. **Per-feature logs for isolated development:**
   ```bash
   --central-log logs/feature-auth.log
   ```

4. **Post-mortem with parser scripts:**
   ```bash
   ./scripts/parse_agent_log_detailed.sh --tools-only logs/run/DIR/verbose.jsonl
   ```

5. **Keep raw logs for deep debugging:**
   - Don't delete `verbose.jsonl` files
   - Use jq for custom analysis when needed

---

## 🐛 Troubleshooting

### Central log not updating
1. Check if logger process is running: `ps aux | grep logger_background`
2. Check monitor.log: `cat logs/run/*/monitor.log | grep logger`
3. Verify logger_background.sh is executable: `ls -l logger_background.sh`

### Parser scripts show nothing
1. Verify log file exists: `ls -la logs/run/*/verbose.jsonl`
2. Check if log is empty: `wc -l logs/run/*/verbose.jsonl`
3. Verify jq is installed: `which jq`

### Orphan tail processes
1. Run test: `./test_orphan_cleanup.sh`
2. Manual cleanup: `pkill -f "tail -f.*verbose.jsonl"`
3. Check for issues with trap handlers

---

## ✅ Summary

You now have three complementary logging tools:

1. **Central Log (`--central-log`)** - Real-time, multi-run, automatic
2. **Parser Scripts** - Post-mortem, detailed, filtering
3. **Raw JSON** - Complete data, custom processing

Use them together for comprehensive agent monitoring and debugging!
