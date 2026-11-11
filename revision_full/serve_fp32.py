"""Published default precision and input padding, with bounded-memory attention."""
import argparse,json,sys,threading,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'upstream/swe-pruner/src'))
import torch
from fastapi import FastAPI
import uvicorn
from swe_pruner.configuration import SwePrunerConfig
from swe_pruner.prune_wrapper import SwePrunerForCodePruning,PruneRequest
from revision_glm.memory_attention import install as install_attention
from revision_full.paper_padding import install as install_padding
parser=argparse.ArgumentParser();parser.add_argument('--original-fusion',action='store_true');args=parser.parse_args()
config=SwePrunerConfig.from_pretrained(ROOT/'models/code-pruner')
config.backbone_model_name_or_path=str(ROOT/'models/qwen-backbone')
# Match the released online_serving.py: no explicit dtype override.
model=SwePrunerForCodePruning.from_pretrained(str(ROOT/'models/code-pruner'),config=config)
assert all(p.dtype==torch.float32 for p in model.parameters())
install_attention(model);install_padding()
if args.original_fusion:
    from revision_full.fusion_attention import install as install_original_fusion
    install_original_fusion(model)
backend='original-mha-tiled-256' if args.original_fusion else 'sdpa-query-tiled-256'
app=FastAPI();lock=threading.Lock()
@app.get('/health')
def health():
    return {'model_loaded':True,'device':str(next(model.parameters()).device),'dtype':str(next(model.parameters()).dtype),
            'input_padding':8192,'attention_backend':backend,'torch':torch.__version__,'allocated_bytes':torch.cuda.memory_allocated()}
@app.post('/prune')
def prune(request:PruneRequest):
    with lock:
        started=time.time();torch.cuda.reset_peak_memory_stats()
        result=model.prune(request)
        record={'seconds':time.time()-started,'input_chars':len(request.code),'origin_tokens':result.origin_token_cnt,
                'left_tokens':result.left_token_cnt,'error':result.error_msg,'peak_allocated_bytes':torch.cuda.max_memory_allocated(),'dtype':'float32','attention_backend':backend}
        folder=ROOT/'runs/precision';folder.mkdir(exist_ok=True)
        with (folder/'pruner_service.jsonl').open('a',encoding='utf-8') as stream:stream.write(json.dumps(record)+'\n')
        return result.model_dump()
if __name__=='__main__':uvicorn.run(app,host='127.0.0.1',port=8000)
