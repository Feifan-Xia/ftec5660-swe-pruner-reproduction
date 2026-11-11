"""Reference pruning coverage and weighted retention from the original archive."""
import json,statistics,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
z=zipfile.ZipFile(ROOT/'runs/author_evidence/swepruner-sweqa-reproduce.zip')
qs=[json.loads(x)['question'] for x in (ROOT/'upstream/downstream_eval/multi_turn/sweqa/questions/streamlink.jsonl').read_text(encoding='utf-8').splitlines()]
indices=json.loads((ROOT/'revision_precision/protocol.json').read_text(encoding='utf-8'))['question_indices']
rows=[]
for name in z.namelist():
    if not(name.startswith('traj-full-glm-pruner/streamlink/') and name.endswith('.traj.json')):continue
    t=json.loads(z.read(name));i=qs.index(t['question'])
    obs=[e['observation'] for e in t['events'] if e.get('observation',{}).get('pruned')]
    rows.append({'index':i,'prune_calls':len(obs),'raw_tokens':sum(o['prune_info']['origin_token_cnt'] for o in obs),
        'kept_tokens':sum(o['prune_info']['left_token_cnt'] for o in obs),
        'changed_outputs':sum(o['original_output']!=o['output'] for o in obs)})
out={}
for label,group in [('all_48',rows),('fixed_eight',[r for r in rows if r['index'] in indices])]:
    raw=sum(r['raw_tokens'] for r in group);kept=sum(r['kept_tokens'] for r in group)
    out[label]={'questions':len(group),'task_activation_percent':100*sum(r['prune_calls']>0 for r in group)/len(group),
        'prune_calls':sum(r['prune_calls'] for r in group),'raw_tokens':raw,'kept_tokens':kept,'weighted_compression_percent':100*(1-kept/raw),
        'changed_outputs':sum(r['changed_outputs'] for r in group)}
out['per_question']=rows
(ROOT/'results/full/author_retention.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k!='per_question'},indent=2))
