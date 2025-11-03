#!/bin/bash
# Launcher script for Voice Training Data Creator
set -euo pipefail

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Ensure virtual environment exists (prefer uv if available)
if [[ ! -d "$SCRIPT_DIR/.venv" ]]; then
  if command -v uv >/dev/null 2>&1; then
    echo "Creating virtual environment with uv..."
    uv venv "$SCRIPT_DIR/.venv"
  else
    echo "Virtualenv not found. Please install uv (pip install uv) or create a venv at $SCRIPT_DIR/.venv" >&2
    python3 -m venv "$SCRIPT_DIR/.venv"
  fi
fi

# Activate virtual environment
source "$SCRIPT_DIR/.venv/bin/activate"

# Bootstrap pip if missing
if ! python -c 'import pip' >/dev/null 2>&1; then
  echo "Bootstrapping pip into venv..."
  python -m ensurepip --upgrade || true
fi

# Upgrade pip (best effort)
python -m pip install --upgrade pip wheel setuptools || true

# Install dependencies (pin includes flet[all]==0.28.3 for desktop runtime)
python -m pip install -r "$SCRIPT_DIR/requirements.txt"

# Run the application
exec python "$SCRIPT_DIR/src/main.py" "$@"
