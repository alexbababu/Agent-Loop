#!/usr/bin/env bash
export UV_PROJECT_ENVIRONMENT="$HOME/.cache/uv-venvs/agent-loop"
SCRIPT="${1:-main.py}"
shift 2>/dev/null || true
uv run "$SCRIPT" "$@"
