#!/bin/bash

# Example: Using Central Logging with Multiple Agents
#
# This script demonstrates how to run multiple Claude agents
# with all their activity consolidated into a single log file.

set -euo pipefail

# Configuration
CENTRAL_LOG="logs/agent.log"
PROMPT_FILE="prompt/coding_agent_prompt.txt"

# Ensure logs directory exists
mkdir -p logs/run

echo "═══════════════════════════════════════════════════════════"
echo "  Central Logging Example"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "This example will:"
echo "1. Run sample Claude agents"
echo "2. Log all activity to: $CENTRAL_LOG"
echo "3. Show you how to monitor in real-time"
echo ""
echo "Press Enter to continue, or Ctrl+C to cancel..."
read

# Start a watcher in the background (optional)
echo ""
echo "Starting log watcher in background..."
echo "You can manually watch with: tail -f $CENTRAL_LOG"
echo ""

# Example 1: Simple task
echo "─────────────────────────────────────────────────────────"
echo "Example 1: Running agent with central logging"
echo "─────────────────────────────────────────────────────────"

RUN_DIR_1="logs/run/$(date +%s)_example-1"
mkdir -p "$RUN_DIR_1"

echo "Starting agent..."
echo "  Output dir: $RUN_DIR_1"
echo "  Central log: $CENTRAL_LOG"
echo ""

# Note: This is an example - modify the prompt as needed
./run_claude_agent.sh \
  --prompt "List all files in the current directory" \
  --output-dir "$RUN_DIR_1" \
  --central-log "$CENTRAL_LOG" \
  --model sonnet \
  --idle-timeout 30

echo ""
echo "Agent 1 completed!"
echo ""

# Example 2: Another task (to show consolidation)
echo "─────────────────────────────────────────────────────────"
echo "Example 2: Running second agent (same central log)"
echo "─────────────────────────────────────────────────────────"

RUN_DIR_2="logs/run/$(date +%s)_example-2"
mkdir -p "$RUN_DIR_2"

echo "Starting agent..."
echo "  Output dir: $RUN_DIR_2"
echo "  Central log: $CENTRAL_LOG"
echo ""

./run_claude_agent.sh \
  --prompt "Show the git status" \
  --output-dir "$RUN_DIR_2" \
  --central-log "$CENTRAL_LOG" \
  --model sonnet \
  --idle-timeout 30

echo ""
echo "Agent 2 completed!"
echo ""

# Show the consolidated results
echo "═══════════════════════════════════════════════════════════"
echo "  Results"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "Both agent runs are consolidated in: $CENTRAL_LOG"
echo ""
echo "View the central log:"
echo "  cat $CENTRAL_LOG"
echo ""
echo "View individual results:"
echo "  cat $RUN_DIR_1/result.txt"
echo "  cat $RUN_DIR_2/result.txt"
echo ""
echo "View raw JSON logs:"
echo "  cat $RUN_DIR_1/verbose.jsonl"
echo "  cat $RUN_DIR_2/verbose.jsonl"
echo ""
echo "Search central log for specific tool:"
echo "  grep 'Tool.*: Bash' $CENTRAL_LOG -A 2"
echo ""
echo "═══════════════════════════════════════════════════════════"
