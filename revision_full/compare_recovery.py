"""Complete fixed-subset recovery comparison and question-cluster uncertainty."""
import json,random,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
indices=read(ROOT/'revision_recovery/protocol.json')['question_indices']
groups={};attempts={};metrics=['score','total_tokens','api_requests','author_rounds','prune_calls','expand_calls']
for stage in ['hint','recovery']:
    groups[stage]=[r for r in read(ROOT/f'results/{stage}/cells.json') if r['repeat']==0]
    attempts[stage]=[r for r in read(ROOT/f'results/{stage}/attempts.json') if r['repeat']==0]
    assert len(groups[stage])==8 and {r['index'] for r in groups[stage]}==set(indices)
    assert all(r['qualified'] and r['score'] is not None for r in groups[stage])
means={}
for stage,g in groups.items():
    means[stage]={k:statistics.mean(r[k] for r in g) for k in metrics}
    means[stage].update(completed_execution_percent=100,first_attempt_execution_percent=100*sum(r['attempt']==0 for r in g)/8,
        expansion_task_percent=100*sum(r['expand_calls']>0 for r in g)/8,
        expanded_chars=sum(r['expanded_chars'] for r in g),repeated_lines=sum(r['repeated_lines'] for r in g),
        all_attempt_total_tokens=sum(r['total_tokens'] for r in attempts[stage]),all_attempt_conservative_api_cost=sum(r['cost'] for r in attempts[stage]))
byq={s:{r['index']:r for r in g} for s,g in groups.items()};effects={}
for metric in metrics[:4]:
    rng=random.Random(5660);samples=[]
    for _ in range(10000):
        picked=rng.choices(indices,k=8)
        b=statistics.mean(byq['hint'][i][metric] for i in picked);p=statistics.mean(byq['recovery'][i][metric] for i in picked)
        samples.append(100*(p/b-1))
    samples.sort();effects[metric]={'relative_percent':100*(means['recovery'][metric]/means['hint'][metric]-1),'cluster_bootstrap_ci95_percent':[samples[249],samples[9749]]}
out={'fixed_indices':indices,'cells':16,'repeats':1,'means':means,'effects':effects,
    'question_pairs':[{'index':i,**{s:{k:byq[s][i][k] for k in metrics+['attempt','expanded_chars','repeated_lines']} for s in groups}} for i in indices],
    'scope':'Task-local raw storage plus bounded line recovery, shared required-hint schema. Sequential diagnostic stage; same eight questions. Timing and independently sampled paths limit causal precision. Exact-string mechanism results remain separate.'}
(ROOT/'results/full/recovery_comparison.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k!='question_pairs'},indent=2))
