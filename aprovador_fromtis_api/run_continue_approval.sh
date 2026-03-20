#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Set custom temp directory for PyInstaller to avoid /tmp cleanup issues
export TMPDIR="$SCRIPT_DIR/tmp"
mkdir -p "$TMPDIR"

# Clean up old PyInstaller extraction directories before starting
# This removes orphaned _MEI* directories from previous runs
echo "$(date '+%Y-%m-%d %H:%M:%S') - Cleaning up old PyInstaller tmp directories..."
find "$TMPDIR" -maxdepth 1 -type d -name "_MEI*" -mtime +1 -exec rm -rf {} \; 2>/dev/null
echo "$(date '+%Y-%m-%d %H:%M:%S') - Cleanup complete"

# Change to script directory
cd "$SCRIPT_DIR"

# Continuously run the aprovador_combined binary
while true; do
    date
    ./aprovador_combined

    # Clean up tmp directories after each run (in case of crash/restart)
    echo "$(date '+%Y-%m-%d %H:%M:%S') - Cleaning up tmp directories after program exit..."
    find "$TMPDIR" -maxdepth 1 -type d -name "_MEI*" -mtime +0 -exec rm -rf {} \; 2>/dev/null
done

