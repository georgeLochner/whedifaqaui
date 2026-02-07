#!/usr/bin/env bash

# Parse and display verbose.jsonl in human-readable format
# Usage: ./parse_agent_log.sh [verbose.jsonl]
#
# This script parses a completed agent log for diagnostics and debugging.
# For real-time monitoring, use --central-log with run_claude_agent.sh instead.

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

# Function to process each JSON line
process_line() {
    local line="$1"

    # Skip empty lines or invalid JSON
    if [[ -z "$line" ]]; then
        return
    fi

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
                    echo -e "${DIM}${CYAN}SYSTEM${RESET} ${DIM}Hook started: ${hook_name}${RESET}"
                    ;;
                hook_response)
                    local hook_name=$(echo "$line" | jq -r '.hook_name // empty')
                    local outcome=$(echo "$line" | jq -r '.outcome // empty')
                    if [[ "$outcome" == "success" ]]; then
                        echo -e "${GREEN}✓${RESET} ${DIM}Hook completed: ${hook_name}${RESET}"
                    else
                        echo -e "${RED}✗${RESET} ${DIM}Hook failed: ${hook_name}${RESET}"
                    fi
                    ;;
                init)
                    local model=$(echo "$line" | jq -r '.model // empty')
                    echo -e "${DIM}${CYAN}SYSTEM${RESET} ${BOLD}Session initialized${RESET} ${DIM}(model: ${model})${RESET}"
                    ;;
            esac
            ;;

        assistant)
            local text=$(echo "$line" | jq -r '.message.content[]? | select(.type=="text") | .text // empty' 2>/dev/null | head -1)
            if [[ -n "$text" ]]; then
                echo -e "${BLUE}CLAUDE:${RESET} ${text}"
            fi

            local tool_name=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_use") | .name // empty' 2>/dev/null | head -1)
            if [[ -n "$tool_name" ]]; then
                echo -e "${MAGENTA}TOOL:${RESET} ${BOLD}${tool_name}${RESET}"

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
            local tool_result=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_result") | . // empty' 2>/dev/null | head -1)
            if [[ -n "$tool_result" ]]; then
                local stdout=$(echo "$tool_result" | jq -r '.content // empty' 2>/dev/null | head -c 200)
                local is_error=$(echo "$line" | jq -r '.tool_use_result.is_error // empty' 2>/dev/null)

                if [[ "$is_error" == "true" ]]; then
                    echo -e "${RED}ERROR:${RESET} Tool execution failed"
                    if [[ -n "$stdout" ]]; then
                        echo -e "  ${DIM}${stdout}${RESET}"
                    fi
                else
                    if [[ -n "$stdout" ]] && [[ "$stdout" != "empty" ]]; then
                        local preview=$(echo "$stdout" | head -c 150 | tr '\n' ' ')
                        if [[ ${#stdout} -gt 150 ]]; then
                            echo -e "${GREEN}✓${RESET} ${DIM}${preview}...${RESET}"
                        else
                            echo -e "${GREEN}✓${RESET} ${DIM}${preview}${RESET}"
                        fi
                    fi
                fi
            fi
            ;;
    esac
}

# Parse log file
echo -e "${BOLD}${CYAN}╔════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${CYAN}║        Claude Agent Log Parser - Diagnostic View          ║${RESET}"
echo -e "${BOLD}${CYAN}╚════════════════════════════════════════════════════════════╝${RESET}"
echo ""
echo -e "${DIM}Parsing: ${LOGFILE}${RESET}"
echo ""

if [[ -s "$LOGFILE" ]]; then
    while IFS= read -r line; do
        process_line "$line"
    done < "$LOGFILE"
    echo ""
    echo -e "${DIM}=== End of log ===${RESET}"
else
    echo -e "${YELLOW}Warning: Log file is empty${RESET}"
fi
