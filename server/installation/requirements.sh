#!/bin/bash
set -e

INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
SERVER_DIR="$(cd "$INSTALL_DIR/.." && pwd)"
VENV_PYTHON="$SERVER_DIR/.venv/bin/python"
REQ_FILE="$INSTALL_DIR/requirements.txt"
TMP_FILE="$INSTALL_DIR/requirements.txt.tmp"

# Ensure .venv exists in server/ before exporting packages
if [ ! -x "$VENV_PYTHON" ]; then
    echo ".venv not found. Run 'bash installation/setup.sh' first." >&2
    exit 1
fi

# Clean up temporary file on exit or error
trap 'rm -f "$TMP_FILE"' EXIT

# Export packages installed inside .venv to a temporary file first, then replace requirements.txt
PIP_REQUIRE_VIRTUALENV=true "$VENV_PYTHON" -m pip freeze > "$TMP_FILE"
mv "$TMP_FILE" "$REQ_FILE"