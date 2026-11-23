#!/bin/bash
set -e

INSTALL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]:-$0}")" && pwd)"
SERVER_DIR="$(cd "$INSTALL_DIR/.." && pwd)"
VENV_DIR="$SERVER_DIR/.venv"
VENV_PYTHON="$VENV_DIR/bin/python"
REQ_FILE="$INSTALL_DIR/requirements.txt"

# Verify requirements.txt exists in server/installation/
if [ ! -f "$REQ_FILE" ]; then
    echo "requirements.txt not found in $INSTALL_DIR" >&2
    exit 1
fi

# Create .venv in server/ if it does not exist
if [ ! -x "$VENV_PYTHON" ]; then
    if [ -n "$VIRTUAL_ENV" ] || [ -n "$CONDA_PREFIX" ]; then
        echo "Deactivate the current virtual environment before creating .venv." >&2
        exit 1
    fi

    if ! command -v python3 >/dev/null 2>&1 || ! python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 11) else 1)"; then
        echo "Python 3.11 or higher is required." >&2
        exit 1
    fi

    python3 -m venv "$VENV_DIR"
    PIP_REQUIRE_VIRTUALENV=true "$VENV_PYTHON" -m pip install --upgrade pip
fi

# Install missing or updated packages strictly inside .venv
PIP_REQUIRE_VIRTUALENV=true "$VENV_PYTHON" -m pip install -r "$REQ_FILE"

# Uninstall packages inside .venv that are no longer listed in requirements.txt
PIP_REQUIRE_VIRTUALENV=true "$VENV_PYTHON" -c "
import re, subprocess, sys
from importlib import metadata
from pathlib import Path

norm = lambda s: re.sub(r'[-_.]+', '-', s).lower()
get_name = lambda s: (m.group(0) if (m := re.match(r'[A-Za-z0-9._-]+', s.strip())) else '')

lines = [l.split('#', 1)[0].strip() for l in Path(sys.argv[1]).read_text(encoding='utf-8').splitlines()]
roots = {'pip', 'setuptools', 'wheel'} | {norm(get_name(l)) for l in lines if l and not l.startswith('-')} - {''}

dists = {norm(d.metadata['Name']): d for d in metadata.distributions() if d.metadata['Name']}
keep = set(roots)
[keep.update({norm(get_name(r)) for p in list(keep) if p in dists and dists[p].requires for r in dists[p].requires} - {''}) for _ in range(len(dists) + 1)]

extra = sorted(set(dists) - keep)
if extra:
    subprocess.check_call([sys.executable, '-m', 'pip', 'uninstall', '-y', *extra])
" "$REQ_FILE"