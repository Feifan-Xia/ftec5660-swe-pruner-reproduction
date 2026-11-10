#!/usr/bin/env bash
set -euo pipefail
export PATH="$HOME/.local/bin:$PATH"
ROOT='/mnt/c/Users/feifa/Documents/ChatGPT/Reproduce Agent'
ENV="$HOME/ftec5660-swe-pruner/.venv"
uv pip install --python "$ENV/bin/python" 'transformers==4.57.1' fastapi uvicorn typer socksio huggingface-hub python-dotenv 'openai==2.8.1' 'openhands-sdk==1.1.0' 'openhands-tools==1.1.0' 'openhands-workspace==1.1.0' 'httpx[socks]' tree-sitter tree-sitter-python
uv pip install --python "$ENV/bin/python" --no-deps -e "$ROOT/upstream/swe-pruner"
"$ENV/bin/python" -c 'import torch; print(torch.__version__, torch.cuda.is_available()); print(torch.cuda.get_device_name(0)); print(torch.ones(2,device="cuda")+1)'
