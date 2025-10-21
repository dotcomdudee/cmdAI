#!/bin/bash
# Quick start script for cmdAI Terminal

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the script directory
cd "$SCRIPT_DIR"

# Install dependencies if needed
if ! python3 -c "import textual" 2>/dev/null; then
    echo "Installing dependencies..."
    pip3 install -e . || pip3 install textual rich httpx pyyaml
fi

# Run the application
python3 -m cmdai_terminal
