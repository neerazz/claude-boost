#!/bin/bash
# Observable Local Skills MCP Server Runner
# This script activates the venv and runs the MCP server

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PYTHON="${SCRIPT_DIR}/venv/bin/python3"

if [ -f "$VENV_PYTHON" ]; then
    exec "$VENV_PYTHON" "${SCRIPT_DIR}/src/mcp_server.py" "$@"
else
    echo "Error: Virtual environment not found. Run:" >&2
    echo "  cd ${SCRIPT_DIR} && /opt/homebrew/bin/python3.14 -m venv venv && source venv/bin/activate && pip install mcp" >&2
    exit 1
fi

