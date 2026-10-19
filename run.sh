#!/usr/bin/env sh
# Cross-Platform POSIX Startup Script (Linux, macOS, BSD, WSL)
set -e

# Resolve directory of this script portably
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# Detect Python executable
if command -v python3 >/dev/null 2>&1; then
    PY_CMD="python3"
elif command -v python >/dev/null 2>&1; then
    PY_CMD="python"
else
    echo "Error: Python is not found in PATH. Please install Python 3.10+." >&2
    exit 1
fi

echo "Launching Xenon Hotel Management via Universal Runner..."
exec "$PY_CMD" "$SCRIPT_DIR/run.py"
