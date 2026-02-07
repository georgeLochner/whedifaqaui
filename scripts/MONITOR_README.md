# Claude Agent Monitor Scripts

Two bash scripts for monitoring Claude agent activity in real-time by parsing `verbose.jsonl` log files.

## Scripts

### 1. `monitor_agent.sh` - Simple Monitor

A lightweight, clean monitoring script that shows the essential agent activity.

**Usage:**
```bash
./monitor_agent.sh [verbose.jsonl]
```

**Features:**
- Clean, minimal output
- Color-coded events (system, Claude messages, tool calls, results)
- Auto-truncates long output for readability
- Shows hook execution and system events
- Real-time following of log file

**Example output:**
```
[14:32:15] SYSTEM Hook started: SessionStart:startup
[14:32:15] ✓ Hook completed: SessionStart:startup
[14:32:16] CLAUDE: I'll start by reading the prompt file...
[14:32:16] TOOL: Read
  Reading: /home/ubuntu/code/whedifaqaui/prompt/coding_agent_prompt.txt
[14:32:17] ✓ # Coding Agent Protocol...
```

---

### 2. `monitor_agent_detailed.sh` - Detailed Monitor

An enhanced monitoring script with extensive formatting and filtering options.

**Usage:**
```bash
./monitor_agent_detailed.sh [options] [verbose.jsonl]
```

**Options:**
- `--full` - Show full output without truncation
- `--tools-only` - Only display tool calls and results
- `--messages-only` - Only display Claude's messages
- `--no-color` - Disable colored output (for piping to files)
- `--timestamps` - Show full timestamps (date + time)
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
[14:32:16] CLAUDE MESSAGE #1:
  I'll start by reading the prompt file and then checking
  the task details.

[14:32:16] TOOL #1: Read
  ID: toolu_018uACucQJXUbxVNvQNHLF9U
  File: /home/ubuntu/code/whedifaqaui/prompt/coding_agent_prompt.txt

  ✓ Result:
    # Coding Agent Protocol

    ## Environment
    All commands run inside Docker containers...
```

---

## Quick Start

1. Make scripts executable (if not already):
   ```bash
   chmod +x monitor_agent.sh monitor_agent_detailed.sh
   ```

2. Monitor the current log file:
   ```bash
   ./monitor_agent.sh verbose.jsonl
   ```

3. Or use the detailed version:
   ```bash
   ./monitor_agent_detailed.sh verbose.jsonl
   ```

4. With options:
   ```bash
   # Only see tool calls
   ./monitor_agent_detailed.sh --tools-only verbose.jsonl

   # Full output with timestamps
   ./monitor_agent_detailed.sh --full --timestamps verbose.jsonl

   # No color for redirecting to file
   ./monitor_agent_detailed.sh --no-color verbose.jsonl > agent_log.txt
   ```

---

## Use Cases

### Simple Monitoring
Use `monitor_agent.sh` when you want:
- Quick overview of agent activity
- Minimal screen clutter
- Fast, lightweight monitoring

### Detailed Analysis
Use `monitor_agent_detailed.sh` when you need:
- Full context of tool parameters
- Debugging specific tool calls
- Detailed error information
- Activity statistics
- Filtered views (tools only, messages only)

---

## Log File Format

Both scripts parse `verbose.jsonl` files, which contain one JSON object per line with the following structure:

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

## Tips

1. **View past activity:** The scripts first process existing log entries, then follow new ones in real-time.

2. **Stop monitoring:** Press `Ctrl+C` to exit.

3. **Multiple terminals:** Run the monitor in one terminal while the agent runs in another.

4. **Save detailed logs:** Use `--no-color` to pipe clean output to a file:
   ```bash
   ./monitor_agent_detailed.sh --no-color --full verbose.jsonl > full_log.txt
   ```

5. **Filter for debugging:** Use `--tools-only` to focus on tool execution when debugging:
   ```bash
   ./monitor_agent_detailed.sh --tools-only verbose.jsonl
   ```

---

## Requirements

- `bash` 4.0+
- `jq` - JSON processor (install with `apt install jq` or `brew install jq`)
- `tail` with `-f` support (standard on Linux/macOS)

---

## Color Legend

- 🔵 **Blue** - Claude messages
- 🟣 **Magenta** - Tool calls
- 🟢 **Green** - Success/completed operations
- 🔴 **Red** - Errors
- 🔷 **Cyan** - System events
- ⚪ **Dim** - Supporting details, timestamps

---

## Troubleshooting

**"jq: command not found"**
```bash
# Ubuntu/Debian
sudo apt install jq

# macOS
brew install jq
```

**"File not found"**
- Ensure you're in the correct directory or provide the full path to `verbose.jsonl`

**No new output appearing**
- Verify the agent is actually running and writing to the log file
- Check that you have the correct log file path

**Garbled output**
- Try `--no-color` if your terminal doesn't support ANSI colors
