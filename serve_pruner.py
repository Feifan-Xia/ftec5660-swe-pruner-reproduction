"""Serve the published pruner with local backbone config and memory telemetry."""
import json
from pathlib import Path
import time
import sys
import threading
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / 'upstream/swe-pruner/src'))
import torch
from fastapi import FastAPI
import uvicorn
from swe_pruner.configuration import SwePrunerConfig
from swe_pruner.prune_wrapper import SwePrunerForCodePruning, PruneRequest

config = SwePrunerConfig.from_pretrained(ROOT / 'models/code-pruner')
config.backbone_model_name_or_path = str(ROOT / 'models/qwen-backbone')
model = SwePrunerForCodePruning.from_pretrained(str(ROOT / 'models/code-pruner'), config=config,
                                              torch_dtype=torch.bfloat16)
inference_lock = threading.Lock()
app = FastAPI()


@app.get('/health')
def health():
    return {'model_loaded': True, 'device': str(next(model.parameters()).device),
            'dtype': str(next(model.parameters()).dtype),
            'allocated_bytes': torch.cuda.memory_allocated(),
            'attention_backend': 'sdpa', 'torch': torch.__version__}


@app.post('/prune')
def prune(request: PruneRequest):
    with inference_lock:
        return prune_locked(request)


def prune_locked(request):
    started = time.time()
    if torch.cuda.is_available():
        torch.cuda.reset_peak_memory_stats()
    result = model.prune(request)
    elapsed = time.time() - started
    record = {'seconds': elapsed, 'input_chars': len(request.code),
              'origin_tokens': result.origin_token_cnt, 'left_tokens': result.left_token_cnt,
              'error': result.error_msg,
              'peak_allocated_bytes': torch.cuda.max_memory_allocated() if torch.cuda.is_available() else 0}
    path = ROOT / 'runs/pruner_service.jsonl'
    path.parent.mkdir(exist_ok=True)
    with path.open('a') as f:
        f.write(json.dumps(record) + '\n')
    return result.model_dump()


if __name__ == '__main__':
    uvicorn.run(app, host='127.0.0.1', port=8000)
