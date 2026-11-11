"""Relative effects on the complete fixed question set; never mix partial arms."""
import argparse,json,random,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--repeats',type=int,choices=[1,3],required=True);args=parser.parse_args()
folder=ROOT/'results/subset'
rows=json.loads((folder/'cells.json').read_text(encoding='utf-8'))
indices=json.loads((ROOT/'revision_subset/protocol.json').read_text(encoding='utf-8'))['question_indices']
rows=[r for r in rows if r['repeat']<args.repeats]
assert len(rows)==len(indices)*2*args.repeats, 'Wait for every fixed paired cell'
assert all(r['score'] is not None and r['qualified'] for r in rows)
groups={m:[r for r in rows if r['mode']==m] for m in ['baseline','pruner']}
result={'questions':indices,'repetitions':args.repeats,'cells':len(rows),'effects':{},'question_means':[]}
for index in indices:
    result['question_means'].append({'index':index,**{m:{k:statistics.mean(r[k] for r in groups[m] if r['index']==index) for k in ['score','total_tokens','author_rounds','api_requests','prune_calls']} for m in groups}})
for metric in ['score','total_tokens','author_rounds','api_requests']:
    baseline=statistics.mean(r[metric] for r in groups['baseline']);pruner=statistics.mean(r[metric] for r in groups['pruner'])
    rng=random.Random(5660);samples=[]
    for _ in range(10000):
        sampled=rng.choices(result['question_means'],k=len(indices))
        b=statistics.mean(q['baseline'][metric] for q in sampled);p=statistics.mean(q['pruner'][metric] for q in sampled)
        samples.append(100*(p/b-1))
    samples.sort()
    result['effects'][metric]={'baseline':baseline,'pruner':pruner,'relative_percent':100*(pruner/baseline-1),'cluster_bootstrap_ci95_percent':[samples[249],samples[9749]]}
result['activation']={'pruner_tasks':sum(r['prune_calls']>0 for r in groups['pruner']),'pruner_task_percent':100*sum(r['prune_calls']>0 for r in groups['pruner'])/len(groups['pruner']),'calls':sum(r['prune_calls'] for r in groups['pruner'])}
(folder/f'effects_r{args.repeats}.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='question_means'},indent=2))
