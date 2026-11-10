#!/usr/bin/env bash
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
AGENT_ENV="${1:-$HOME/.venvs/ftec5660-agent}"
command -v uv >/dev/null
if [[ ! -x "$AGENT_ENV/bin/python" ]]; then
    uv venv --python 3.12 "$AGENT_ENV"
fi
uv pip install --python "$AGENT_ENV/bin/python" -r "$ROOT/requirements-agent.txt"
"$AGENT_ENV/bin/python" "$ROOT/prepare_upstream.py"
"$AGENT_ENV/bin/python" -c 'from openhands.sdk import LLM; print("Agent SDK import succeeded")'
