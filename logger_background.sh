#!/usr/bin/env bash

# Background Logger for Claude Agent Runs
# Usage: logger_background.sh <verbose.jsonl> <output.log> <run_id>
#
# This script runs in the background, parsing verbose.jsonl as the agent runs
# and appending human-readable output to a central log file.

set -euo pipefail

VERBOSE_FILE="${1:-}"
OUTPUT_LOG="${2:-}"
RUN_ID="${3:-unknown}"

if [[ -z "$VERBOSE_FILE" ]] || [[ -z "$OUTPUT_LOG" ]]; then
    echo "Usage: $0 <verbose.jsonl> <output.log> <run_id>" >&2
    exit 1
fi

# Wait for verbose file to be created
WAIT_COUNT=0
while [[ ! -f "$VERBOSE_FILE" ]] && [[ $WAIT_COUNT -lt 30 ]]; do
    sleep 0.1
    WAIT_COUNT=$((WAIT_COUNT + 1))
done

if [[ ! -f "$VERBOSE_FILE" ]]; then
    echo "ERROR: Verbose file not created: $VERBOSE_FILE" >&2
    exit 1
fi

# Initialize log section for this run
{
    echo ""
    echo "═══════════════════════════════════════════════════════════════════"
    echo "RUN: $RUN_ID | Started: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "Log: $VERBOSE_FILE"
    echo "═══════════════════════════════════════════════════════════════════"
    echo ""
} >> "$OUTPUT_LOG"

# Track state
TOOL_COUNT=0
MESSAGE_COUNT=0
TAIL_PID=""
COUNTS_FILE=""

# Cleanup function to kill tail subprocess
cleanup_logger() {
    if [[ -n "$TAIL_PID" ]] && kill -0 "$TAIL_PID" 2>/dev/null; then
        kill "$TAIL_PID" 2>/dev/null || true
        wait "$TAIL_PID" 2>/dev/null || true
    fi
}

# Trap to ensure tail is always killed on abnormal exit.
# Don't delete COUNTS_FILE here — the main code path reads it for the footer.
# On normal exit, the main code reads and deletes it. On abnormal exit (TERM
# from parent), the trap fires first; if it deleted the file, the main code
# (which resumes after the trap handler returns) would find nothing to read.
trap cleanup_logger EXIT INT TERM

# Function to format timestamp
format_time() {
    date +"%H:%M:%S"
}

# Function to process a single JSON line
process_line() {
    local line="$1"

    # Skip empty lines or invalid JSON
    if [[ -z "$line" ]]; then
        return
    fi

    # Test if line is valid JSON
    if ! echo "$line" | jq -e . >/dev/null 2>&1; then
        return
    fi

    local type=$(echo "$line" | jq -r '.type // empty' 2>/dev/null)
    local subtype=$(echo "$line" | jq -r '.subtype // empty' 2>/dev/null)

    case "$type" in
        system)
            case "$subtype" in
                init)
                    local model=$(echo "$line" | jq -r '.model // empty' 2>/dev/null)
                    echo "[$(format_time)] System initialized (model: $model)"
                    ;;
                hook_response)
                    local hook_name=$(echo "$line" | jq -r '.hook_name // empty' 2>/dev/null)
                    local outcome=$(echo "$line" | jq -r '.outcome // empty' 2>/dev/null)
                    if [[ "$outcome" == "success" ]]; then
                        echo "[$(format_time)] Hook completed: $hook_name"
                    else
                        echo "[$(format_time)] Hook FAILED: $hook_name"
                    fi
                    ;;
            esac
            ;;

        assistant)
            # Check for text messages
            local text=$(echo "$line" | jq -r '.message.content[]? | select(.type=="text") | .text // empty' 2>/dev/null | head -1)
            if [[ -n "$text" ]]; then
                MESSAGE_COUNT=$((MESSAGE_COUNT + 1))
                echo ""
                echo "[$(format_time)] Claude Message #$MESSAGE_COUNT:"
                # Truncate long messages
                if [[ ${#text} -gt 300 ]]; then
                    echo "${text:0:300}..."
                else
                    echo "$text"
                fi
                echo ""
            fi

            # Check for tool calls
            local tool_name=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_use") | .name // empty' 2>/dev/null | head -1)
            if [[ -n "$tool_name" ]]; then
                TOOL_COUNT=$((TOOL_COUNT + 1))
                echo "[$(format_time)] Tool #$TOOL_COUNT: $tool_name"

                # Show key details for common tools
                case "$tool_name" in
                    Bash)
                        local command=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_use") | .input.command // empty' 2>/dev/null)
                        if [[ -n "$command" ]] && [[ "$command" != "empty" ]]; then
                            # Truncate long commands
                            if [[ ${#command} -gt 100 ]]; then
                                echo "  $ ${command:0:100}..."
                            else
                                echo "  $ $command"
                            fi
                        fi
                        ;;
                    Read)
                        local file_path=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_use") | .input.file_path // empty' 2>/dev/null)
                        if [[ -n "$file_path" ]] && [[ "$file_path" != "empty" ]]; then
                            echo "  Reading: $file_path"
                        fi
                        ;;
                    Write)
                        local file_path=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_use") | .input.file_path // empty' 2>/dev/null)
                        if [[ -n "$file_path" ]] && [[ "$file_path" != "empty" ]]; then
                            echo "  Writing: $file_path"
                        fi
                        ;;
                    Edit)
                        local file_path=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_use") | .input.file_path // empty' 2>/dev/null)
                        if [[ -n "$file_path" ]] && [[ "$file_path" != "empty" ]]; then
                            echo "  Editing: $file_path"
                        fi
                        ;;
                    Glob|Grep)
                        local pattern=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_use") | .input.pattern // empty' 2>/dev/null)
                        if [[ -n "$pattern" ]] && [[ "$pattern" != "empty" ]]; then
                            echo "  Pattern: $pattern"
                        fi
                        ;;
                    Task)
                        local subagent=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_use") | .input.subagent_type // empty' 2>/dev/null)
                        local description=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_use") | .input.description // empty' 2>/dev/null)
                        if [[ -n "$subagent" ]] && [[ "$subagent" != "empty" ]]; then
                            echo "  Subagent: $subagent"
                        fi
                        if [[ -n "$description" ]] && [[ "$description" != "empty" ]]; then
                            echo "  Description: $description"
                        fi
                        ;;
                esac
            fi
            ;;

        user)
            # Check for tool results
            local is_error=$(echo "$line" | jq -r '.tool_use_result.is_error // empty' 2>/dev/null)
            if [[ "$is_error" == "true" ]]; then
                local stderr=$(echo "$line" | jq -r '.tool_use_result.stderr // empty' 2>/dev/null)
                echo "  ✗ ERROR"
                if [[ -n "$stderr" ]] && [[ "$stderr" != "empty" ]]; then
                    # Truncate error output
                    if [[ ${#stderr} -gt 200 ]]; then
                        echo "  ${stderr:0:200}..."
                    else
                        echo "  $stderr"
                    fi
                fi
            elif [[ -n "$is_error" ]]; then
                # Only show success for tools that had output
                local stdout=$(echo "$line" | jq -r '.tool_use_result.stdout // empty' 2>/dev/null)
                if [[ -n "$stdout" ]] && [[ "$stdout" != "empty" ]]; then
                    echo "  ✓ Success"
                    # Optionally show truncated output
                    if [[ ${#stdout} -gt 150 ]]; then
                        echo "  ${stdout:0:150}..."
                    fi
                fi
            fi
            ;;
    esac
}

# Create temp file for sharing counts between pipeline subshell and parent.
# The while loop in a pipeline runs in a subshell, so its variable increments
# are invisible to the parent process that writes the footer.
COUNTS_FILE=$(mktemp)
echo "0 0" > "$COUNTS_FILE"

# Follow the verbose file from the beginning and process all lines (existing + new)
# Using -n +1 reads from line 1, avoiding a race condition where lines written
# between an initial read and tail -f -n 0 would be silently lost.
tail -f -n +1 "$VERBOSE_FILE" 2>/dev/null | while IFS= read -r line; do
    process_line "$line"
    echo "$MESSAGE_COUNT $TOOL_COUNT" > "$COUNTS_FILE"
done >> "$OUTPUT_LOG" &

TAIL_PID=$!

# Wait for parent process (run_claude_agent.sh) to exit
while true; do
    sleep 2

    if ! kill -0 $PPID 2>/dev/null; then
        # Parent exited — allow pipeline time to process remaining lines
        sleep 2
        break
    fi
done

# Cleanup (trap will also ensure this happens)
cleanup_logger

# Read final counts from pipeline subshell via temp file
if [[ -n "$COUNTS_FILE" ]] && [[ -f "$COUNTS_FILE" ]]; then
    read MESSAGE_COUNT TOOL_COUNT < "$COUNTS_FILE" 2>/dev/null || true
    rm -f "$COUNTS_FILE"
    COUNTS_FILE=""
fi

# Write completion footer
{
    echo ""
    echo "───────────────────────────────────────────────────────────────────"
    echo "Run completed: $(date '+%Y-%m-%d %H:%M:%S')"
    echo "Messages: $MESSAGE_COUNT | Tool calls: $TOOL_COUNT"
    echo "═══════════════════════════════════════════════════════════════════"
    echo ""
} >> "$OUTPUT_LOG"

exit 0
