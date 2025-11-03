#!/bin/bash
# Launcher script for Voice Training Data Creator

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate virtual environment
source "$SCRIPT_DIR/.venv/bin/activate"

# Run the application
python "$SCRIPT_DIR/src/main.py" "$@"
