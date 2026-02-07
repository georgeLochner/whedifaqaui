# Claude Agent Log Parser Scripts

Two bash scripts for parsing completed `verbose.jsonl` logs from Claude agent runs. These are diagnostic tools for post-mortem analysis and debugging.

**For real-time monitoring:** Use `--central-log` option with `run_claude_agent.sh` (see `../CENTRAL_LOGGING.md`)

---

## Scripts

### 1. `parse_agent_log.sh` - Simple Parser

A lightweight parser that shows the essential agent activity in a clean format.

**Usage:**
```bash
./parse_agent_log.sh path/to/verbose.jsonl
```

**Features:**
- Clean, minimal output
- Color-coded events (system, Claude messages, tool calls, results)
- Auto-truncates long output for readability
- Shows hook execution and system events
- Fast parsing of completed logs

**Example output:**
```
SYSTEM Hook started: SessionStart:startup
✓ Hook completed: SessionStart:startup
SYSTEM Session initialized (model: claude-opus-4-6)
CLAUDE: I'll start by reading the prompt file...
TOOL: Read
  Reading: /home/ubuntu/code/whedifaqaui/prompt/coding_agent_prompt.txt
✓ Success

=== End of log ===
```

---

### 2. `parse_agent_log_detailed.sh` - Detailed Parser

An enhanced parser with extensive formatting and filtering options for in-depth analysis.

**Usage:**
```bash
./parse_agent_log_detailed.sh [options] path/to/verbose.jsonl
```

**Options:**
- `--full` - Show full output without truncation
- `--tools-only` - Only display tool calls and results
- `--messages-only` - Only display Claude's messages
- `--no-color` - Disable colored output (for piping to files)
- `--help` - Show help message

**Features:**
- Detailed tool call information with parameters
- Numbered messages and tool calls for tracking
- Statistics summary (message count, tool calls, errors)
- Formatted output with proper indentation
- Special handling for different tool types (Bash, Read, Write, Edit, etc.)
- Error highlighting
- Context-aware output formatting

**Example output:**
```
CLAUDE MESSAGE #1:
  I'll start by reading the prompt file and then checking
  the task details.

TOOL #1: Read
  ID: toolu_018uACucQJXUbxVNvQNHLF9U
  File: /home/ubuntu/code/whedifaqaui/prompt/coding_agent_prompt.txt

  ✓ Result:
    # Coding Agent Protocol

    ## Environment
    All commands run inside Docker containers...

═══════════════════════════════════════════════════════════════════════
Summary: Messages: 5, Tool calls: 12, Errors: 0
═══════════════════════════════════════════════════════════════════════
```

---

## Quick Start

1. Parse a completed agent log:
   ```bash
   cd scripts
   ./parse_agent_log.sh ../logs/run/1234_task-name/verbose.jsonl
   ```

2. Detailed parsing with options:
   ```bash
   # Only see tool calls
   ./parse_agent_log_detailed.sh --tools-only ../logs/run/1234_task-name/verbose.jsonl

   # Full output without truncation
   ./parse_agent_log_detailed.sh --full ../logs/run/1234_task-name/verbose.jsonl

   # Export to text file without colors
   ./parse_agent_log_detailed.sh --no-color verbose.jsonl > analysis.txt
   ```

---

## Use Cases

### Quick Overview
Use `parse_agent_log.sh` when you want:
- Fast scan of what an agent did
- Minimal screen clutter
- Quick verification that a task completed

### Deep Debugging
Use `parse_agent_log_detailed.sh` when you need:
- Full context of tool parameters
- Debugging specific tool calls
- Detailed error analysis
- Filtering specific activity (tools only, messages only)
- Statistics (how many messages, tool calls, errors)

---

## Common Workflows

### Debugging Failed Runs

```bash
# Find the run directory
ls -lt logs/run/ | head -5

# Quick overview to see what happened
./scripts/parse_agent_log.sh logs/run/1234_task-name/verbose.jsonl

# If issues found, get detailed view
./scripts/parse_agent_log_detailed.sh --full logs/run/1234_task-name/verbose.jsonl

# Focus on just the tool calls to see what commands ran
./scripts/parse_agent_log_detailed.sh --tools-only logs/run/1234_task-name/verbose.jsonl
```

### Analyzing Successful Runs

```bash
# See what tools were used
./scripts/parse_agent_log_detailed.sh --tools-only logs/run/1234_task-name/verbose.jsonl | grep "TOOL #"

# Count bash commands
./scripts/parse_agent_log_detailed.sh --tools-only logs/run/1234_task-name/verbose.jsonl | grep "TOOL.*Bash" | wc -l

# Export full analysis for documentation
./scripts/parse_agent_log_detailed.sh --full --no-color logs/run/1234_task-name/verbose.jsonl > analysis.txt
```

### Comparing Multiple Runs

```bash
# Parse multiple logs to compare
for run in logs/run/*; do
  echo "=== $run ==="
  ./scripts/parse_agent_log.sh "$run/verbose.jsonl" | grep "Tool #" | wc -l
done
```

---

## Real-time Monitoring vs. Post-Mortem Parsing

| Need | Solution |
|------|----------|
| **Watch agent as it runs** | Use `--central-log logs/agent.log` with `run_claude_agent.sh`, then `tail -f logs/agent.log` |
| **Analyze completed run** | Use these parser scripts on the specific `verbose.jsonl` |
| **Debug specific tools/messages** | Use parser scripts with `--tools-only` or `--messages-only` filters |
| **Compare multiple runs** | Parse each with scripts and compare outputs |

See `../CENTRAL_LOGGING.md` for real-time monitoring setup.

---

## Log File Format

Both scripts parse `verbose.jsonl` files created by Claude CLI with `--output-format stream-json`:

```json
{"type": "assistant", "message": {...}, "session_id": "..."}
{"type": "user", "message": {...}, "tool_use_result": {...}}
{"type": "system", "subtype": "init", ...}
```

**Event types:**
- `system` - Hook execution, session initialization
- `assistant` - Claude's messages and tool calls
- `user` - Tool results and responses

---

## Options Reference

### parse_agent_log.sh
- Takes one argument: path to `verbose.jsonl`
- No options (simple by design)
- Outputs to stdout

### parse_agent_log_detailed.sh
| Option | Description | Example |
|--------|-------------|---------|
| `--full` | No truncation of long output | Full file contents, long commands |
| `--tools-only` | Only show tool calls/results | Debug what commands ran |
| `--messages-only` | Only show Claude's messages | See agent's reasoning |
| `--no-color` | Plain text output | Pipe to file or grep |
| `--help` | Show help | - |

---

## Requirements

- `bash` 4.0+
- `jq` - JSON processor (install with `apt install jq` or `brew install jq`)

---

## Color Legend

- 🔵 **Blue** - Claude messages
- 🟣 **Magenta** - Tool calls
- 🟢 **Green** - Success/completed operations
- 🔴 **Red** - Errors
- 🔷 **Cyan** - System events
- ⚪ **Dim** - Supporting details

Use `--no-color` to disable colors.

---

## Troubleshooting

### "jq: command not found"
```bash
# Ubuntu/Debian
sudo apt install jq

# macOS
brew install jq
```

### "File not found"
- Verify the path to `verbose.jsonl` exists
- Use `ls -la logs/run/*/verbose.jsonl` to find logs

### Empty or incomplete output
- The log file may be empty or from a crashed run
- Check `monitor.log` in the same directory for run status
- Verify the agent completed (or at least started writing logs)

### Garbled output
- Try `--no-color` if your terminal doesn't support ANSI colors
- Some terminals may need UTF-8 encoding enabled

---

## Tips

1. **Pipe to less for scrolling:**
   ```bash
   ./parse_agent_log_detailed.sh verbose.jsonl | less -R
   ```
   (The `-R` preserves colors)

2. **Search within output:**
   ```bash
   ./parse_agent_log_detailed.sh verbose.jsonl | grep -i "error"
   ```

3. **Count specific events:**
   ```bash
   ./parse_agent_log_detailed.sh --tools-only verbose.jsonl | grep "TOOL #" | wc -l
   ```

4. **Export for sharing:**
   ```bash
   ./parse_agent_log_detailed.sh --no-color --full verbose.jsonl > share.txt
   ```

5. **Quick check if run succeeded:**
   ```bash
   ./parse_agent_log.sh verbose.jsonl | tail -20
   ```
