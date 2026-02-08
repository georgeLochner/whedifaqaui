#!/bin/bash
set -euo pipefail

# Claude CLI Agent Wrapper with Activity Monitoring
# Usage: ./run_claude_agent.sh --prompt "..." --output-dir DIR [options]
#
# The prompt is passed directly to the Claude CLI agent.

# Default values
MODEL="opus"
RESUME=""
EXTENDED_THINKING=""
IDLE_TIMEOUT=60
MAX_RUNTIME=3600
SKIP_PERMISSIONS=true
MONITOR_INTERVAL=5
CENTRAL_LOG=""  # Optional central log file for all agent runs

# Usage function
usage() {
    cat << EOF
Usage: $0 --prompt "..." --output-dir DIR [options]

Required:
    --prompt "..."          Prompt to send to the Claude CLI agent
    --output-dir DIR        Directory to store output logs (must exist)

Optional:
    --resume ID            Resume a previous conversation by session ID
    --model MODEL          Model to use (sonnet|opus|haiku) [default: opus]
    --extended-thinking N  Enable extended thinking with N tokens
    --idle-timeout N       Seconds of idle time before termination [default: 60]
    --max-runtime N        Maximum runtime in seconds [default: 3600]
    --monitor-interval N   Seconds between activity checks [default: 5]
    --central-log FILE     Append parsed activity to central log file (optional)
    --skip-permissions     Add --dangerously-skip-permissions flag [default: true]
    --no-skip-permissions  Require permission prompts (disable skip-permissions)
    --help                 Show this help message

Output Files (created in --output-dir):
    result.txt             Final agent output (includes session_id and free_space)
    verbose.jsonl          Detailed JSON activity log
    monitor.log            Activity monitoring log
    agent.pid              PID file (removed on completion)
    logger.pid             Logger PID file (if --central-log used, removed on completion)

Exit Codes:
    0 - Success
    1 - Agent went idle
    2 - Maximum runtime exceeded
    3 - Agent crashed or error
    4 - Invalid arguments
EOF
    exit 4
}

# Parse arguments
PROMPT=""
OUTPUT_DIR=""
while [[ $# -gt 0 ]]; do
    case $1 in
        --prompt)
            PROMPT="$2"
            shift 2
            ;;
        --output-dir)
            OUTPUT_DIR="$2"
            shift 2
            ;;
        --model)
            MODEL="$2"
            shift 2
            ;;
        --resume)
            RESUME="$2"
            shift 2
            ;;
        --extended-thinking)
            EXTENDED_THINKING="$2"
            shift 2
            ;;
        --idle-timeout)
            IDLE_TIMEOUT="$2"
            shift 2
            ;;
        --max-runtime)
            MAX_RUNTIME="$2"
            shift 2
            ;;
        --monitor-interval)
            MONITOR_INTERVAL="$2"
            shift 2
            ;;
        --central-log)
            CENTRAL_LOG="$2"
            shift 2
            ;;
        --skip-permissions)
            SKIP_PERMISSIONS=true
            shift
            ;;
        --no-skip-permissions)
            SKIP_PERMISSIONS=false
            shift
            ;;
        --help)
            usage
            ;;
        *)
            echo "Error: Unknown option $1" >&2
            usage
            ;;
    esac
done

# Validate required arguments
if [[ -z "$PROMPT" ]]; then
    echo "Error: --prompt is required" >&2
    usage
fi

if [[ -z "$OUTPUT_DIR" ]]; then
    echo "Error: --output-dir is required" >&2
    usage
fi

if [[ ! -d "$OUTPUT_DIR" ]]; then
    echo "Error: Output directory does not exist: $OUTPUT_DIR" >&2
    exit 4
fi

# Set up output directory paths
WORK_DIR="$OUTPUT_DIR"
RESULT_FILE="$WORK_DIR/result.txt"
VERBOSE_FILE="$WORK_DIR/verbose.jsonl"
MONITOR_LOG="$WORK_DIR/monitor.log"
AGENT_PID_FILE="$WORK_DIR/agent.pid"
LOGGER_PID_FILE="$WORK_DIR/logger.pid"

# Cleanup function (kills agent and logger if interrupted, preserves all logs)
cleanup() {
    local exit_code=$?

    # Kill logger if still running
    if [[ -f "$LOGGER_PID_FILE" ]]; then
        local logger_pid=$(cat "$LOGGER_PID_FILE")
        if kill -0 "$logger_pid" 2>/dev/null; then
            kill "$logger_pid" 2>/dev/null || true
            # Wait briefly for logger to finish writing
            sleep 0.5
        fi
        rm -f "$LOGGER_PID_FILE"
    fi

    # Kill agent if still running
    if [[ -f "$AGENT_PID_FILE" ]]; then
        local pid=$(cat "$AGENT_PID_FILE")
        if kill -0 "$pid" 2>/dev/null; then
            kill -9 "$pid" 2>/dev/null || true
        fi
        rm -f "$AGENT_PID_FILE"
    fi

    echo "Logs preserved in: $WORK_DIR" >&2

    exit $exit_code
}

trap cleanup EXIT INT TERM

# Build Claude CLI command
CLAUDE_ARGS=(
    -p "$PROMPT"
    --model "$MODEL"
    --settings '{"autoCompact": false}'
)

if [[ "$SKIP_PERMISSIONS" == "true" ]]; then
    CLAUDE_ARGS+=(--dangerously-skip-permissions)
fi

if [[ -n "$RESUME" ]]; then
    CLAUDE_ARGS+=(--resume "$RESUME")
fi

# Set extended thinking environment variable if specified
if [[ -n "$EXTENDED_THINKING" ]]; then
    export MAX_THINKING_TOKENS="$EXTENDED_THINKING"
fi

# Log monitoring configuration
echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting Claude agent" >> "$MONITOR_LOG"
echo "  Model: $MODEL" >> "$MONITOR_LOG"
if [[ -n "$RESUME" ]]; then
    echo "  Resuming session: $RESUME" >> "$MONITOR_LOG"
fi
echo "  Idle timeout: ${IDLE_TIMEOUT}s" >> "$MONITOR_LOG"
echo "  Max runtime: ${MAX_RUNTIME}s" >> "$MONITOR_LOG"
if [[ -n "$EXTENDED_THINKING" ]]; then
    echo "  Extended thinking: $EXTENDED_THINKING tokens" >> "$MONITOR_LOG"
fi

# Run Claude CLI with JSON stream output to verbose log
# stdout (JSON stream) -> verbose.jsonl, stderr -> verbose.jsonl (appended)
claude "${CLAUDE_ARGS[@]}" --verbose --output-format stream-json > "$VERBOSE_FILE" 2>&1 &
AGENT_PID=$!
echo "$AGENT_PID" > "$AGENT_PID_FILE"

# Start background logger if central log requested
if [[ -n "$CENTRAL_LOG" ]]; then
    # Ensure central log directory exists
    CENTRAL_LOG_DIR=$(dirname "$CENTRAL_LOG")
    mkdir -p "$CENTRAL_LOG_DIR"

    # Generate run ID from output directory name
    RUN_ID=$(basename "$OUTPUT_DIR")

    # Find logger script (look in same directory as this script)
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    LOGGER_SCRIPT="$SCRIPT_DIR/logger_background.sh"

    if [[ -x "$LOGGER_SCRIPT" ]]; then
        "$LOGGER_SCRIPT" "$VERBOSE_FILE" "$CENTRAL_LOG" "$RUN_ID" &
        LOGGER_PID=$!
        echo "$LOGGER_PID" > "$LOGGER_PID_FILE"
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Background logger started (PID: $LOGGER_PID)" >> "$MONITOR_LOG"
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Central log: $CENTRAL_LOG" >> "$MONITOR_LOG"
    else
        echo "WARNING: Background logger not found at $LOGGER_SCRIPT" >&2
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Background logger not found" >> "$MONITOR_LOG"
    fi
fi

# Monitor agent activity
START_TIME=$(date +%s)
LAST_ACTIVITY_TIME=$START_TIME
IDLE_COUNT=0

while kill -0 "$AGENT_PID" 2>/dev/null; do
    CURRENT_TIME=$(date +%s)
    ELAPSED=$((CURRENT_TIME - START_TIME))

    # Check max runtime
    if [[ $ELAPSED -ge $MAX_RUNTIME ]]; then
        echo "ERROR: Maximum runtime (${MAX_RUNTIME}s) exceeded" >&2
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Max runtime exceeded" >> "$MONITOR_LOG"
        kill -9 "$AGENT_PID" 2>/dev/null || true
        exit 2
    fi

    # Check for new activity in verbose output
    # Look for recent JSON events (tool use, thinking, etc.)
    RECENT_ACTIVITY=false
    if [[ -f "$VERBOSE_FILE" ]]; then
        # Check if file was modified in last monitoring interval
        FILE_MTIME=$(stat -c %Y "$VERBOSE_FILE" 2>/dev/null || echo 0)
        TIME_SINCE_MODIFICATION=$((CURRENT_TIME - FILE_MTIME))

        if [[ $TIME_SINCE_MODIFICATION -le $MONITOR_INTERVAL ]]; then
            RECENT_ACTIVITY=true
        fi
    fi

    # Check CPU activity as backup indicator
    CPU_PERCENT=$(ps -p "$AGENT_PID" -o %cpu= 2>/dev/null | tr -d ' ' | cut -d. -f1)
    if [[ -n "$CPU_PERCENT" ]] && [[ "$CPU_PERCENT" -gt 0 ]]; then
        RECENT_ACTIVITY=true
    fi

    # Update idle counter
    if [[ "$RECENT_ACTIVITY" == "true" ]]; then
        IDLE_COUNT=0
        LAST_ACTIVITY_TIME=$CURRENT_TIME
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Activity detected (CPU: ${CPU_PERCENT}%)" >> "$MONITOR_LOG"
    else
        IDLE_COUNT=$((IDLE_COUNT + MONITOR_INTERVAL))
        TIME_SINCE_ACTIVITY=$((CURRENT_TIME - LAST_ACTIVITY_TIME))
        echo "$(date '+%Y-%m-%d %H:%M:%S') - Idle for ${TIME_SINCE_ACTIVITY}s (CPU: ${CPU_PERCENT}%)" >> "$MONITOR_LOG"

        if [[ $IDLE_COUNT -ge $IDLE_TIMEOUT ]]; then
            echo "ERROR: Agent idle for ${IDLE_COUNT}s (threshold: ${IDLE_TIMEOUT}s)" >&2
            echo "$(date '+%Y-%m-%d %H:%M:%S') - Idle timeout reached, terminating" >> "$MONITOR_LOG"
            kill -9 "$AGENT_PID" 2>/dev/null || true
            exit 1
        fi
    fi

    sleep "$MONITOR_INTERVAL"
done

# Wait for agent to finish and get exit code
wait "$AGENT_PID"
AGENT_EXIT_CODE=$?

echo "$(date '+%Y-%m-%d %H:%M:%S') - Agent completed (exit code: $AGENT_EXIT_CODE)" >> "$MONITOR_LOG"

# Extract final result from JSON stream and write to result.txt
# The stream-json output ends with a "result" type message containing the final output
SESSION_ID=""
RESULT_IS_ERROR=""
if [[ -f "$VERBOSE_FILE" ]]; then
    if command -v jq &> /dev/null; then
        # Extract the .result field from the final "result" type message
        # Use grep to filter to JSON lines only (start with {), then parse with jq
        grep '^{' "$VERBOSE_FILE" | jq -r 'select(.type == "result") | .result // empty' 2>/dev/null > "$RESULT_FILE"
        # Extract is_error to check for failure (boolean: true/false)
        RESULT_IS_ERROR=$(grep '^{' "$VERBOSE_FILE" | jq -r 'select(.type == "result") | .is_error' 2>/dev/null)
        # Use the --resume session ID if available, otherwise extract from init message
        if [[ -n "$RESUME" ]]; then
            SESSION_ID="$RESUME"
        else
            SESSION_ID=$(grep '^{' "$VERBOSE_FILE" | jq -r 'select(.type == "system" and .subtype == "init") | .session_id // empty' 2>/dev/null | head -1)
        fi
    else
        # Fallback without jq: use python to parse JSON
        # Python writes result directly to file (avoids delimiter issues with
        # multi-line content) and outputs session_id and is_error on separate lines.
        PYTHON_OUTPUT=$(python3 -c "
import json, sys
session_id = ''
is_error = ''
result = ''
for line in open('$VERBOSE_FILE'):
    try:
        obj = json.loads(line)
        if obj.get('type') == 'system' and obj.get('subtype') == 'init' and not session_id:
            session_id = obj.get('session_id', '')
        if obj.get('type') == 'result':
            result = obj.get('result', '')
            is_error = str(obj.get('is_error', '')).lower()
    except: pass
with open('$RESULT_FILE', 'w') as f:
    f.write(result)
print(session_id)
print(is_error)
" 2>/dev/null) || {
            echo "WARNING: Neither jq nor python3 available for JSON parsing" >&2
            echo "See $VERBOSE_FILE for raw output" > "$RESULT_FILE"
        }
        if [[ -n "$RESUME" ]]; then
            SESSION_ID="$RESUME"
        else
            SESSION_ID=$(echo "$PYTHON_OUTPUT" | sed -n '1p')
        fi
        RESULT_IS_ERROR=$(echo "$PYTHON_OUTPUT" | sed -n '2p')
    fi
fi

# Check if agent crashed (non-zero exit code)
if [[ $AGENT_EXIT_CODE -ne 0 ]]; then
    echo "ERROR: Agent exited with code $AGENT_EXIT_CODE" >&2
    echo "--- Verbose log tail ---" >&2
    tail -20 "$VERBOSE_FILE" >&2 2>/dev/null || true
    exit 3
fi

# Check if result indicates an error
if [[ "$RESULT_IS_ERROR" == "true" ]]; then
    echo "ERROR: Agent completed with is_error=true" >&2
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Result is_error: true" >> "$MONITOR_LOG"
    cat "$RESULT_FILE" >&2 2>/dev/null || true
    exit 3
fi

# Get context usage info using the session_id
FREE_SPACE=""
if [[ -n "$SESSION_ID" ]]; then
    # Run /context command to get usage info
    CONTEXT_OUTPUT=$(claude -r "$SESSION_ID" -p "/context" --verbose --output-format stream-json 2>/dev/null)
    if [[ -n "$CONTEXT_OUTPUT" ]]; then
        # Extract Free space from the context output
        # The content is in a user message with the markdown table
        FREE_SPACE=$(echo "$CONTEXT_OUTPUT" | grep '^{' | jq -r 'select(.type == "user") | .message.content // ""' 2>/dev/null | grep -oP 'Free space \| \K[0-9.]+k? \| [0-9.]+%' | head -1 | sed 's/ | / (/' | sed 's/$/)/')
    fi
fi

# Append session_id and free_space to result.txt
if [[ -n "$SESSION_ID" ]] || [[ -n "$FREE_SPACE" ]]; then
    echo "" >> "$RESULT_FILE"
    echo "---" >> "$RESULT_FILE"
    [[ -n "$SESSION_ID" ]] && echo "session_id: $SESSION_ID" >> "$RESULT_FILE"
    [[ -n "$FREE_SPACE" ]] && echo "free_space: $FREE_SPACE" >> "$RESULT_FILE"
fi

# Output result to stdout
cat "$RESULT_FILE"

# Success
exit 0
