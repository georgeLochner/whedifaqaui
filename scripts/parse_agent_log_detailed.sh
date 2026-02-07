#!/usr/bin/env bash

# Enhanced Claude Agent Log Parser - Detailed diagnostic viewer
# Usage: ./parse_agent_log_detailed.sh [options] [verbose.jsonl]
#
# This script parses a completed agent log for diagnostics and debugging.
# For real-time monitoring, use --central-log with run_claude_agent.sh instead.
#
# Options:
#   --full           Show full output (no truncation)
#   --tools-only     Only show tool calls
#   --messages-only  Only show Claude messages
#   --no-color       Disable colored output
#   --help           Show this help

set -euo pipefail

# Default options
FULL_OUTPUT=false
TOOLS_ONLY=false
MESSAGES_ONLY=false
NO_COLOR=false
LOGFILE=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --full)
            FULL_OUTPUT=true
            shift
            ;;
        --tools-only)
            TOOLS_ONLY=true
            shift
            ;;
        --messages-only)
            MESSAGES_ONLY=true
            shift
            ;;
        --no-color)
            NO_COLOR=true
            shift
            ;;
        --help)
            head -n 14 "$0" | tail -n 13
            exit 0
            ;;
        *)
            LOGFILE="$1"
            shift
            ;;
    esac
done

# Default to verbose.jsonl if not specified
LOGFILE="${LOGFILE:-verbose.jsonl}"

if [[ ! -f "$LOGFILE" ]]; then
    echo "Error: File '$LOGFILE' not found"
    exit 1
fi

# ANSI color codes
if [[ "$NO_COLOR" == "true" ]]; then
    BOLD=""
    DIM=""
    RED=""
    GREEN=""
    YELLOW=""
    BLUE=""
    MAGENTA=""
    CYAN=""
    RESET=""
else
    BOLD='\033[1m'
    DIM='\033[2m'
    RED='\033[0;31m'
    GREEN='\033[0;32m'
    YELLOW='\033[0;33m'
    BLUE='\033[0;34m'
    MAGENTA='\033[0;35m'
    CYAN='\033[0;36m'
    RESET='\033[0m'
fi

# Counters
TOOL_CALLS=0
MESSAGES=0
ERRORS=0

# Function to truncate text
truncate_text() {
    local text="$1"
    local max_len="${2:-150}"

    if [[ "$FULL_OUTPUT" == "true" ]]; then
        echo "$text"
    else
        if [[ ${#text} -gt $max_len ]]; then
            echo "${text:0:$max_len}..."
        else
            echo "$text"
        fi
    fi
}

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
            if [[ "$TOOLS_ONLY" == "true" ]] || [[ "$MESSAGES_ONLY" == "true" ]]; then
                return
            fi

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
                    local cwd=$(echo "$line" | jq -r '.cwd // empty')
                    echo -e "${CYAN}SYSTEM${RESET} ${BOLD}Session initialized${RESET}"
                    echo -e "  ${DIM}Model: ${model}${RESET}"
                    echo -e "  ${DIM}CWD: ${cwd}${RESET}"
                    ;;
            esac
            ;;

        assistant)
            # Check if this is a message with text content
            local text=$(echo "$line" | jq -r '.message.content[]? | select(.type=="text") | .text // empty' 2>/dev/null | head -1)
            if [[ -n "$text" ]] && [[ "$TOOLS_ONLY" != "true" ]]; then
                MESSAGES=$((MESSAGES + 1))
                echo ""
                echo -e "${BLUE}${BOLD}CLAUDE MESSAGE #${MESSAGES}:${RESET}"
                echo -e "${text}" | fold -s -w 80 | sed 's/^/  /'
                echo ""
            fi

            # Check for tool use
            local tool_name=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_use") | .name // empty' 2>/dev/null | head -1)
            if [[ -n "$tool_name" ]] && [[ "$MESSAGES_ONLY" != "true" ]]; then
                TOOL_CALLS=$((TOOL_CALLS + 1))
                local tool_id=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_use") | .id // empty' 2>/dev/null | head -1)

                echo -e "${MAGENTA}${BOLD}TOOL #${TOOL_CALLS}: ${tool_name}${RESET}"
                echo -e "  ${DIM}ID: ${tool_id}${RESET}"

                # Show specific tool details
                case "$tool_name" in
                    Bash)
                        local command=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_use") | .input.command // empty' 2>/dev/null)
                        local description=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_use") | .input.description // empty' 2>/dev/null)
                        if [[ -n "$command" ]] && [[ "$command" != "empty" ]]; then
                            echo -e "  ${YELLOW}Command:${RESET}"
                            echo "$command" | fold -s -w 76 | sed 's/^/    /'
                        fi
                        if [[ -n "$description" ]] && [[ "$description" != "empty" ]] && [[ "$description" != "null" ]]; then
                            echo -e "  ${DIM}Description: ${description}${RESET}"
                        fi
                        ;;
                    Read)
                        local file_path=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_use") | .input.file_path // empty' 2>/dev/null)
                        local offset=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_use") | .input.offset // empty' 2>/dev/null)
                        local limit=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_use") | .input.limit // empty' 2>/dev/null)
                        if [[ -n "$file_path" ]] && [[ "$file_path" != "empty" ]]; then
                            echo -e "  ${YELLOW}File:${RESET} ${file_path}"
                        fi
                        if [[ -n "$offset" ]] && [[ "$offset" != "empty" ]] && [[ "$offset" != "null" ]]; then
                            echo -e "  ${DIM}Offset: ${offset}, Limit: ${limit}${RESET}"
                        fi
                        ;;
                    Write)
                        local file_path=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_use") | .input.file_path // empty' 2>/dev/null)
                        local content_len=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_use") | .input.content | length // 0' 2>/dev/null)
                        if [[ -n "$file_path" ]] && [[ "$file_path" != "empty" ]]; then
                            echo -e "  ${YELLOW}File:${RESET} ${file_path}"
                        fi
                        if [[ "$content_len" != "0" ]]; then
                            echo -e "  ${DIM}Content length: ${content_len} chars${RESET}"
                        fi
                        ;;
                    Edit)
                        local file_path=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_use") | .input.file_path // empty' 2>/dev/null)
                        local old_string=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_use") | .input.old_string // empty' 2>/dev/null | head -c 50)
                        local new_string=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_use") | .input.new_string // empty' 2>/dev/null | head -c 50)
                        if [[ -n "$file_path" ]] && [[ "$file_path" != "empty" ]]; then
                            echo -e "  ${YELLOW}File:${RESET} ${file_path}"
                        fi
                        if [[ -n "$old_string" ]] && [[ "$old_string" != "empty" ]]; then
                            echo -e "  ${DIM}Old: ${old_string}...${RESET}"
                            echo -e "  ${DIM}New: ${new_string}...${RESET}"
                        fi
                        ;;
                    Glob)
                        local pattern=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_use") | .input.pattern // empty' 2>/dev/null)
                        local path=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_use") | .input.path // empty' 2>/dev/null)
                        if [[ -n "$pattern" ]] && [[ "$pattern" != "empty" ]]; then
                            echo -e "  ${YELLOW}Pattern:${RESET} ${pattern}"
                        fi
                        if [[ -n "$path" ]] && [[ "$path" != "empty" ]] && [[ "$path" != "null" ]]; then
                            echo -e "  ${DIM}Path: ${path}${RESET}"
                        fi
                        ;;
                    Grep)
                        local pattern=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_use") | .input.pattern // empty' 2>/dev/null)
                        local path=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_use") | .input.path // empty' 2>/dev/null)
                        local output_mode=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_use") | .input.output_mode // empty' 2>/dev/null)
                        if [[ -n "$pattern" ]] && [[ "$pattern" != "empty" ]]; then
                            echo -e "  ${YELLOW}Pattern:${RESET} ${pattern}"
                        fi
                        if [[ -n "$path" ]] && [[ "$path" != "empty" ]] && [[ "$path" != "null" ]]; then
                            echo -e "  ${DIM}Path: ${path}${RESET}"
                        fi
                        if [[ -n "$output_mode" ]] && [[ "$output_mode" != "empty" ]] && [[ "$output_mode" != "null" ]]; then
                            echo -e "  ${DIM}Mode: ${output_mode}${RESET}"
                        fi
                        ;;
                    Task)
                        local subagent_type=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_use") | .input.subagent_type // empty' 2>/dev/null)
                        local description=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_use") | .input.description // empty' 2>/dev/null)
                        local prompt=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_use") | .input.prompt // empty' 2>/dev/null | head -c 100)
                        if [[ -n "$subagent_type" ]] && [[ "$subagent_type" != "empty" ]]; then
                            echo -e "  ${YELLOW}Subagent:${RESET} ${subagent_type}"
                        fi
                        if [[ -n "$description" ]] && [[ "$description" != "empty" ]]; then
                            echo -e "  ${YELLOW}Description:${RESET} ${description}"
                        fi
                        if [[ -n "$prompt" ]] && [[ "$prompt" != "empty" ]]; then
                            echo -e "  ${DIM}Prompt: $(truncate_text "$prompt" 80)${RESET}"
                        fi
                        ;;
                    *)
                        # Generic tool display - show input if full output requested
                        if [[ "$FULL_OUTPUT" == "true" ]]; then
                            local tool_input=$(echo "$line" | jq -c '.message.content[]? | select(.type=="tool_use") | .input // empty' 2>/dev/null | head -1)
                            if [[ -n "$tool_input" ]] && [[ "$tool_input" != "empty" ]]; then
                                echo "$tool_input" | jq '.' 2>/dev/null | sed 's/^/  /' || true
                            fi
                        fi
                        ;;
                esac
            fi
            ;;

        user)
            if [[ "$MESSAGES_ONLY" == "true" ]]; then
                return
            fi

            # Check for tool results
            local tool_result=$(echo "$line" | jq -r '.message.content[]? | select(.type=="tool_result") | . // empty' 2>/dev/null | head -1)
            if [[ -n "$tool_result" ]]; then
                local is_error=$(echo "$line" | jq -r '.tool_use_result.is_error // empty' 2>/dev/null)
                local stdout=$(echo "$line" | jq -r '.tool_use_result.stdout // empty' 2>/dev/null)
                local stderr=$(echo "$line" | jq -r '.tool_use_result.stderr // empty' 2>/dev/null)

                if [[ "$is_error" == "true" ]]; then
                    ERRORS=$((ERRORS + 1))
                    echo -e "${RED}${BOLD}  ✗ ERROR${RESET}"
                    if [[ -n "$stderr" ]] && [[ "$stderr" != "empty" ]]; then
                        echo -e "  ${RED}${stderr}${RESET}" | fold -s -w 76 | sed 's/^/    /'
                    fi
                    if [[ -n "$stdout" ]] && [[ "$stdout" != "empty" ]]; then
                        echo -e "  ${RED}${stdout}${RESET}" | fold -s -w 76 | sed 's/^/    /'
                    fi
                else
                    # For non-error results, show output
                    if [[ -n "$stdout" ]] && [[ "$stdout" != "empty" ]]; then
                        local preview=$(truncate_text "$stdout" 300)
                        echo -e "${GREEN}  ✓ Result:${RESET}"
                        echo -e "${DIM}${preview}${RESET}" | fold -s -w 76 | sed 's/^/    /'
                    else
                        echo -e "${GREEN}  ✓ Success${RESET}"
                    fi
                fi
                echo ""
            fi
            ;;
    esac
}

# Print header
echo -e "${BOLD}${CYAN}╔═══════════════════════════════════════════════════════════════════╗${RESET}"
echo -e "${BOLD}${CYAN}║     Claude Agent Log Parser - Detailed Diagnostic View           ║${RESET}"
echo -e "${BOLD}${CYAN}╚═══════════════════════════════════════════════════════════════════╝${RESET}"
echo ""
echo -e "${DIM}Parsing: ${LOGFILE}${RESET}"
if [[ "$TOOLS_ONLY" == "true" ]]; then
    echo -e "${DIM}Mode: Tools only${RESET}"
elif [[ "$MESSAGES_ONLY" == "true" ]]; then
    echo -e "${DIM}Mode: Messages only${RESET}"
else
    echo -e "${DIM}Mode: Full activity${RESET}"
fi
echo ""

# Process log file
if [[ -s "$LOGFILE" ]]; then
    while IFS= read -r line; do
        process_line "$line"
    done < "$LOGFILE"
    echo ""
    echo -e "${DIM}═══════════════════════════════════════════════════════════════════════${RESET}"
    echo -e "${DIM}Summary: Messages: ${MESSAGES}, Tool calls: ${TOOL_CALLS}, Errors: ${ERRORS}${RESET}"
    echo -e "${DIM}═══════════════════════════════════════════════════════════════════════${RESET}"
else
    echo -e "${YELLOW}Warning: Log file is empty${RESET}"
fi
