"""Compare full and query-tiled fusion on fixed short and long real code inputs."""
import sys,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
import torch
from serve_pruner import model
from swe_pruner.prune_wrapper import build_input_for_llm
from revision_glm.memory_attention import install
cases=[('Why are current and previous hours accepted?','src/streamlink/plugins/albavision.py',4096),('How does fail_unhandled_requests affect request interception?','src/streamlink/webbrowser/cdp/client.py',4096),('How does fail_unhandled_requests affect request interception?','src/streamlink/webbrowser/cdp/client.py',8192)]
rows=[]
for query,path,limit in cases:
 code=(ROOT/'data/streamlink'/path).read_text(encoding='utf-8')
 code='\n'.join(f'{i:6}\t{line}' for i,line in enumerate(code.splitlines(),1))
 inputs=build_input_for_llm(query,code,model.tokenizer,instruction=model.instruction,max_length=limit)
 def evaluate():
  torch.cuda.empty_cache();torch.cuda.reset_peak_memory_stats();started=time.time()
  with torch.no_grad(),torch.amp.autocast('cuda',dtype=torch.float16):
   out=model(input_ids=inputs['input_ids'].to('cuda'),attention_mask=inputs['attention_mask'].to('cuda'))
  probs=out.token_logits.float().sigmoid().cpu();score=out.score_logits.float().cpu()
  return probs,score,time.time()-started,torch.cuda.max_memory_allocated()
 reference_originals=install(query_tile=512) if limit>4096 else []
 base,score,seconds,peak=evaluate()
 for obj,name,forward in reference_originals:setattr(obj,name,forward)
 originals=install(model)
 other,other_score,other_seconds,other_peak=evaluate()
 for obj,name,forward in originals:setattr(obj,name,forward)
 rows.append({'path':path,'reference':'tiled512' if limit>4096 else 'full_sdpa','input_tokens':inputs['input_ids'].shape[1],'baseline_seconds':seconds,'tiled_seconds':other_seconds,'baseline_peak_bytes':peak,'tiled_peak_bytes':other_peak,'max_probability_delta':float((base-other).abs().max()),'threshold_0_5_disagreements':int(((base>=.5)!=(other>=.5)).sum()),'score_delta':float((score-other_score).abs().max())})
 (ROOT/'runs/glm/attention_validation.json').write_text(json.dumps(rows,indent=2),encoding='utf-8');print(json.dumps(rows[-1]),flush=True)
