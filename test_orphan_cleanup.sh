#!/bin/bash

# Test script to verify logger_background.sh doesn't leave orphan processes
# Usage: ./test_orphan_cleanup.sh

set -euo pipefail

echo "Testing logger_background.sh cleanup..."
echo ""

# Create a test directory
TEST_DIR="logs/test_cleanup_$(date +%s)"
mkdir -p "$TEST_DIR"

# Create a dummy verbose.jsonl with some test data
cat > "$TEST_DIR/verbose.jsonl" << 'EOF'
{"type":"system","subtype":"init","model":"test-model","session_id":"test-123"}
{"type":"assistant","message":{"content":[{"type":"text","text":"Test message"}]}}
EOF

# Start the logger in background
echo "Starting logger_background.sh..."
./logger_background.sh "$TEST_DIR/verbose.jsonl" "logs/test_agent.log" "test-run" &
LOGGER_PID=$!
echo "Logger PID: $LOGGER_PID"

# Give it a moment to start
sleep 1

# Check what processes the logger spawned
echo ""
echo "Logger and its children:"
ps -o pid,ppid,command --forest | grep -A 5 "$LOGGER_PID" | grep -v grep || echo "No processes found"

# Count tail processes before killing
TAIL_COUNT_BEFORE=$(pgrep -f "tail -f.*$TEST_DIR/verbose.jsonl" | wc -l)
echo ""
echo "Tail processes before kill: $TAIL_COUNT_BEFORE"

# Kill the logger (simulating run_claude_agent.sh cleanup)
echo ""
echo "Killing logger (PID $LOGGER_PID)..."
kill "$LOGGER_PID"

# Wait a moment for cleanup
sleep 1

# Check if any tail processes are left
TAIL_COUNT_AFTER=$(pgrep -f "tail -f.*$TEST_DIR/verbose.jsonl" | wc -l)
echo "Tail processes after kill: $TAIL_COUNT_AFTER"

# Verify cleanup
echo ""
if [[ $TAIL_COUNT_AFTER -eq 0 ]]; then
    echo "✓ SUCCESS: No orphan processes left!"
    echo "The trap cleanup is working correctly."
else
    echo "✗ FAILURE: Found $TAIL_COUNT_AFTER orphan tail process(es)"
    echo "Orphaned processes:"
    pgrep -f "tail -f.*$TEST_DIR/verbose.jsonl" -a || true
    echo ""
    echo "Cleaning up manually..."
    pkill -f "tail -f.*$TEST_DIR/verbose.jsonl" || true
fi

# Cleanup test files
echo ""
echo "Cleaning up test files..."
rm -rf "$TEST_DIR"

echo "Test complete!"
