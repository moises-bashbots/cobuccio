#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Set custom temp directory for PyInstaller to avoid /tmp cleanup issues
export TMPDIR="$SCRIPT_DIR/tmp"
mkdir -p "$TMPDIR"

# Clean up old PyInstaller extraction directories (older than 1 day)
# This removes orphaned _MEI* directories from previous runs
find "$TMPDIR" -maxdepth 1 -type d -name "_MEI*" -mtime +1 -exec rm -rf {} \; 2>/dev/null

# Define the binary to be executed
BINARY="$SCRIPT_DIR/aprovador_combined"
BINARY_NAME="aprovador_combined"
PIDFILE="$SCRIPT_DIR/${BINARY_NAME}.pid"
LOGFILE="$SCRIPT_DIR/${BINARY_NAME}.log"

# Function to check if process is running
is_running() {
    if [ -f "$PIDFILE" ]; then
        PID=$(cat "$PIDFILE")
        if ps -p "$PID" > /dev/null 2>&1; then
            # Check if it's actually our binary
            if ps -p "$PID" -o cmd= | grep -q "$BINARY_NAME"; then
                return 0
            fi
        fi
        # PID file exists but process is not running - clean up
        rm -f "$PIDFILE"
    fi
    return 1
}

# Check if already running
if is_running; then
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $BINARY_NAME is already running (PID: $(cat $PIDFILE))"
    exit 0
fi

# Start the binary in background
echo "$(date '+%Y-%m-%d %H:%M:%S') - Starting $BINARY_NAME..."
cd "$SCRIPT_DIR"
nohup "$BINARY" >> "$LOGFILE" 2>&1 &
PID=$!

# Save PID to file
echo $PID > "$PIDFILE"

echo "$(date '+%Y-%m-%d %H:%M:%S') - $BINARY_NAME started with PID: $PID"
echo "$(date '+%Y-%m-%d %H:%M:%S') - Log file: $LOGFILE"

