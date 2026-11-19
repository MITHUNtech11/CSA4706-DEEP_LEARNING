#!/usr/bin/env bash
# ==============================================================================
# Hospital Clinical RAG RBAC Server Launcher (Linux / macOS)
# ==============================================================================

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

if [ -f "../.venv/bin/python" ]; then
    PYTHON_EXE="../.venv/bin/python"
elif [ -f ".venv/bin/python" ]; then
    PYTHON_EXE=".venv/bin/python"
else
    PYTHON_EXE="python3"
fi

echo "====================================================================="
echo " HOSPITAL RAG ROLE-BASED ACCESS CONTROL - PRODUCTION SERVER"
echo "====================================================================="
echo "[INFO] Using Python: $PYTHON_EXE"
echo "[INFO] Starting server on http://0.0.0.0:8000 ..."

exec "$PYTHON_EXE" -m uvicorn src.api.app:app --host 0.0.0.0 --port 8000
