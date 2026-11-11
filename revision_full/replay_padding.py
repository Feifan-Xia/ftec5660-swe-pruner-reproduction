"""Replay every historical filtered observation with the published input padding."""
import json
from pathlib import Path
import sys
import time
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import torch
from serve_pruner import model
import swe_pruner.prune_wrapper as wrapper
from revision_glm.memory_attention import install
install(model)
original_build=wrapper.build_input_for_llm

def padded_build(*args,**kwargs):
    inputs=original_build(*args,**kwargs)
    max_length=kwargs.get('max_length',args[3] if len(args)>3 else 8192)
    padding=max_length-inputs['input_ids'].shape[1]
    inputs['input_ids']=torch.nn.functional.pad(inputs['input_ids'],(0,padding),value=model.tokenizer.pad_token_id)
    inputs['attention_mask']=torch.nn.functional.pad(inputs['attention_mask'],(0,padding),value=0)
    return inputs

def read(p):return json.loads(p.read_text(encoding='utf-8'))
out=ROOT/'runs/full/diagnostics/padding'
out.mkdir(parents=True,exist_ok=True)
records=[]
for path in sorted((ROOT/'runs/glm/pinned/formal').glob('*/q*/attempt*/trajectories/streamlink/*.traj.json')):
    for ordinal,event in enumerate(read(path)['events']):
        observation=event.get('observation',{})
        if not observation.get('pruned'):continue
        info=observation['prune_info']
        request=wrapper.PruneRequest(query=info['context_focus_question'],code=observation['original_output'],threshold=.5)
        key=f'{path.parts[-6]}-{path.parts[-5]}-e{ordinal}'
        target=out/(key+'.json')
        if target.exists():
            records.append(read(target));continue
        row={'key':key,'source':path.relative_to(ROOT).as_posix(),'event':ordinal,'query':request.query,'raw_chars':len(request.code)}
        for name,build in [('unpad',original_build),('paper_pad',padded_build)]:
            wrapper.build_input_for_llm=build
            torch.cuda.empty_cache();torch.cuda.reset_peak_memory_stats()
            started=time.time();result=model.prune(request)
            row[name]={'seconds':time.time()-started,'kept_frags':result.kept_frags,'left_tokens':result.left_token_cnt,
                       'peak_bytes':torch.cuda.max_memory_allocated(),'error':result.error_msg,
                       'matches_historical_text':result.pruned_code==observation['output']}
        old=set(row['unpad']['kept_frags']);new=set(row['paper_pad']['kept_frags'])
        row['line_decision_changes']=len(old^new)
        row['added_lines']=sorted(new-old);row['removed_lines']=sorted(old-new)
        target.write_text(json.dumps(row,indent=2,ensure_ascii=False),encoding='utf-8')
        records.append(row)
        print(json.dumps({k:v for k,v in row.items() if k not in ('unpad','paper_pad','query')}),flush=True)
wrapper.build_input_for_llm=original_build
summary={'observations':len(records),'historical_exact_replays':sum(r['unpad']['matches_historical_text'] for r in records),
         'changed_observations':sum(r['line_decision_changes']>0 for r in records),
         'changed_line_decisions':sum(r['line_decision_changes'] for r in records),'records':records}
(ROOT/'results/full/padding_replay.json').write_text(json.dumps(summary,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in summary.items() if k!='records'}),flush=True)
