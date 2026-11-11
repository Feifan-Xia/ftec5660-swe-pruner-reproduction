"""Schema-matched filtering effect, with all eight fixed questions and retry costs."""
import json,random,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
indices=read(ROOT/'revision_hintfull/protocol.json')['question_indices']
groups={};attempts={}
for label,stage in [('matched_full','hintfull'),('required_pruner','hint')]:
    groups[label]=[r for r in read(ROOT/f'results/{stage}/cells.json') if r['repeat']==0]
    attempts[label]=[r for r in read(ROOT/f'results/{stage}/attempts.json') if r['repeat']==0]
    assert len(groups[label])==8 and {r['index'] for r in groups[label]}==set(indices)
    assert all(r['qualified'] and r['score'] is not None for r in groups[label])
means={};effects={}
for label,group in groups.items():
    means[label]={k:statistics.mean(r[k] for r in group) for k in ['score','total_tokens','api_requests','author_rounds','seconds','prune_calls']}
    means[label].update(completed_sr_percent=100,first_attempt_sr_percent=100*sum(r['attempt']==0 for r in group)/8,
        all_attempt_mean_tokens=sum(r['total_tokens'] for r in attempts[label])/8,
        all_attempt_known_api_cost=sum(r['cost'] for r in attempts[label]),
        actual_pruning_task_percent=100*sum(r['prune_calls']>0 for r in group)/8)
    raw=sum(r['raw_pruned_tokens'] for r in group);kept=sum(r['kept_pruned_tokens'] for r in group)
    means[label]['source_compression_percent']=100*(1-kept/raw) if raw else None
byq={m:{r['index']:r for r in g} for m,g in groups.items()}
for metric in ['score','total_tokens','api_requests','author_rounds']:
    rng=random.Random(5660);samples=[]
    for _ in range(10000):
        picked=rng.choices(indices,k=8)
        b=statistics.mean(byq['matched_full'][i][metric] for i in picked)
        p=statistics.mean(byq['required_pruner'][i][metric] for i in picked)
        samples.append(100*(p/b-1))
    samples.sort()
    effects[metric]={'relative_percent':100*(means['required_pruner'][metric]/means['matched_full'][metric]-1),
                     'cluster_bootstrap_ci95_percent':[samples[249],samples[9749]]}
out={'fixed_indices':indices,'cells':16,'repeats':1,'means':means,'effects':effects,
    'question_pairs':[{'index':i,**{m:{k:byq[m][i][k] for k in ['score','total_tokens','api_requests','prune_calls','attempt']} for m in groups}} for i in indices],
    'interpretation':'Mechanism diagnostic: identical required-hint tool schema, active pruning versus full-output executor. Independently ordered online runs, eight question clusters. Includes failure/retry sensitivity; timing reflects shared GPU and network scheduling.'}
(ROOT/'results/full/activation_control_comparison.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k!='question_pairs'},indent=2))
