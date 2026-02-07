#!/usr/bin/env bash

# Monitor verbose.jsonl and display human-readable output
# Usage: ./monitor_agent.sh [verbose.jsonl]

set -euo pipefail

LOGFILE="${1:-verbose.jsonl}"

if [[ ! -f "$LOGFILE" ]]; then
    echo "Error: File '$LOGFILE' not found"
    exit 1
fi

# ANSI color codes
BOLD='\033[1m'
DIM='\033[2m'
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
MAGENTA='\033[0;35m'
CYAN='\033[0;36m'
RESET='\033[0m'

# Function to format timestamp
format_time() {
    date +"%H:%M:%S"
}

# Function to process each JSON line
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
                hook_started)
                    local hook_name=$(echo "$line" | jq -r '.hook_name // empty')
                    echo -e "${DIM}[$(format_time)] ${CYAN}SYSTEM${RESET} ${DIM}Hook started: ${hook_name}${RESET}"
                    ;;
                hook_response)
                    local hook_name=$(echo "$line" | jq -r '.hook_name // empty')
                    local outcome=$(echo "$line" | jq -r '.outcome // empty')
                    if [[ "$outcome" == "success" ]]; then
                        echo -e "${DIM}[$(format_time)] ${GREEN}✓${RESET} ${DIM}Hook completed: ${hook_name}${RESET}"
                    else
                        echo -e "${DIM}[$(format_time)] ${RED}✗${RESET} ${DIM}Hook failed: ${hook_name}${RESET}"
                    fi
                    ;;
                init)
                    local model=$(echo "$line" | jq -r '.model // empty')
                    echo -e "${DIM}[$(format_time)] ${CYAN}SYSTEM${RESET} ${BOLD}Session initialized${RESET} ${DIM}(model: ${model})${RESET}"
                    ;;
            esac
            ;;

        assistant)
            # Check if this is a message with text content
            local text=$(echo "$line" | jq -r '.message.content[]? | select(.type=="text") | .text // empty' 2>/dev/null | head -1)
            if [[ -n "$text" ]]; then
                echo -e "${DIM}[$(format_time)]${RESET} ${BLUE}CLAUDE:${RESET} ${text}"
            fi

            # Check for tool use
            local tool_name=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_use") | .name // empty' 2>/dev/null | head -1)
            if [[ -n "$tool_name" ]]; then
                echo -e "${DIM}[$(format_time)]${RESET} ${MAGENTA}TOOL:${RESET} ${BOLD}${tool_name}${RESET}"

                # Show specific tool details
                case "$tool_name" in
                    Bash)
                        local command=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_use") | .input.command // empty' 2>/dev/null)
                        if [[ -n "$command" ]] && [[ "$command" != "empty" ]]; then
                            echo -e "  ${DIM}$ ${command}${RESET}"
                        fi
                        ;;
                    Read)
                        local file_path=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_use") | .input.file_path // empty' 2>/dev/null)
                        if [[ -n "$file_path" ]] && [[ "$file_path" != "empty" ]]; then
                            echo -e "  ${DIM}Reading: ${file_path}${RESET}"
                        fi
                        ;;
                    Write)
                        local file_path=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_use") | .input.file_path // empty' 2>/dev/null)
                        if [[ -n "$file_path" ]] && [[ "$file_path" != "empty" ]]; then
                            echo -e "  ${DIM}Writing: ${file_path}${RESET}"
                        fi
                        ;;
                    Edit)
                        local file_path=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_use") | .input.file_path // empty' 2>/dev/null)
                        if [[ -n "$file_path" ]] && [[ "$file_path" != "empty" ]]; then
                            echo -e "  ${DIM}Editing: ${file_path}${RESET}"
                        fi
                        ;;
                    Glob|Grep)
                        local pattern=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_use") | .input.pattern // empty' 2>/dev/null)
                        if [[ -n "$pattern" ]] && [[ "$pattern" != "empty" ]]; then
                            echo -e "  ${DIM}Pattern: ${pattern}${RESET}"
                        fi
                        ;;
                esac
            fi
            ;;

        user)
            # Check for tool results
            local tool_result=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_result") | . // empty' 2>/dev/null | head -1)
            if [[ -n "$tool_result" ]]; then
                local stdout=$(echo "$tool_result" | jq -r '.content // empty' 2>/dev/null | head -c 200)
                local is_error=$(echo "$line" | jq -r '.tool_use_result.is_error // .tool_use_result.isImage // empty' 2>/dev/null)

                if [[ "$is_error" == "true" ]]; then
                    echo -e "${DIM}[$(format_time)]${RESET} ${RED}ERROR:${RESET} Tool execution failed"
                    if [[ -n "$stdout" ]]; then
                        echo -e "  ${DIM}${stdout}...${RESET}"
                    fi
                else
                    # For non-error results, show first bit of output
                    if [[ -n "$stdout" ]] && [[ "$stdout" != "empty" ]]; then
                        # Truncate long output
                        local preview=$(echo "$stdout" | head -c 150 | tr '\n' ' ')
                        if [[ ${#stdout} -gt 150 ]]; then
                            echo -e "${DIM}[$(format_time)]${RESET} ${GREEN}✓${RESET} ${DIM}${preview}...${RESET}"
                        else
                            echo -e "${DIM}[$(format_time)]${RESET} ${GREEN}✓${RESET} ${DIM}${preview}${RESET}"
                        fi
                    fi
                fi
            fi
            ;;
    esac
}

# Main monitoring loop
echo -e "${BOLD}${CYAN}╔════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${CYAN}║        Claude Agent Monitor - Real-time Activity          ║${RESET}"
echo -e "${BOLD}${CYAN}╚════════════════════════════════════════════════════════════╝${RESET}"
echo ""
echo -e "${DIM}Monitoring: ${LOGFILE}${RESET}"
echo -e "${DIM}Press Ctrl+C to stop${RESET}"
echo ""

# First, show existing content
if [[ -s "$LOGFILE" ]]; then
    echo -e "${DIM}=== Processing existing log entries ===${RESET}"
    while IFS= read -r line; do
        process_line "$line"
    done < "$LOGFILE"
    echo -e "${DIM}=== Now monitoring for new entries ===${RESET}"
    echo ""
fi

# Then follow for new content
tail -f -n 0 "$LOGFILE" | while IFS= read -r line; do
    process_line "$line"
done
