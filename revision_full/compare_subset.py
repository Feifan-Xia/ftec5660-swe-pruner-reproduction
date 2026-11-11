"""Analyze all fixed paired cells and label the separately run policy intervention."""
import argparse,json,random,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--repeats',type=int,choices=[1,3],required=True);args=parser.parse_args()
indices=json.loads((ROOT/'revision_precision/protocol.json').read_text(encoding='utf-8'))['question_indices']
rows=[]
for stage in ['precision','hint']:
    source=json.loads((ROOT/f'results/{stage}/cells.json').read_text(encoding='utf-8'))
    for row in source:
        if row['repeat']>=args.repeats:continue
        row=dict(row,condition=('required_hint' if stage=='hint' else row['mode']),stage=stage)
        rows.append(row)
groups={m:[r for r in rows if r['condition']==m] for m in ['baseline','pruner','required_hint']}
for mode,group in groups.items():
    assert len(group)==8*args.repeats,(mode,len(group))
    assert {(r['index'],r['repeat']) for r in group}=={(i,r) for i in indices for r in range(args.repeats)}
    assert all(r['qualified'] and r['score'] is not None for r in group)
metrics=['score','total_tokens','author_rounds','api_requests','prune_calls']
means={mode:{metric:statistics.mean(r[metric] for r in group) for metric in metrics} for mode,group in groups.items()}
question_means={i:{mode:{metric:statistics.mean(r[metric] for r in group if r['index']==i) for metric in metrics} for mode,group in groups.items()} for i in indices}
effects={}
for comparison,left,right in [('optional_vs_full','baseline','pruner'),('required_vs_full','baseline','required_hint'),('required_vs_optional','pruner','required_hint')]:
    effects[comparison]={}
    for metric in metrics[:4]:
        rng=random.Random(5660);samples=[]
        for _ in range(10000):
            selected=rng.choices(indices,k=len(indices))
            a=statistics.mean(question_means[i][left][metric] for i in selected)
            b=statistics.mean(question_means[i][right][metric] for i in selected)
            samples.append(100*(b/a-1))
        samples.sort()
        effects[comparison][metric]={'relative_percent':100*(means[right][metric]/means[left][metric]-1),'cluster_bootstrap_ci95_percent':[samples[249],samples[9749]]}
out={'repeats':args.repeats,'indices':indices,'unique_cells':len(rows),'means':means,'effects':effects,
     'activation':{m:{'task_percent':100*sum(r['prune_calls']>0 for r in g)/len(g),'prune_calls':sum(r['prune_calls'] for r in g)} for m,g in groups.items()},
     'question_means':question_means,
     'interpretation':'Fixed diagnostic subset; eight question clusters. Required-hint is a separate policy modification. Shared controls are used once. Historical stages remain separate. Intervals measure question sampling variation, with limited support at n=8.'}
dest=ROOT/f'results/full/subset_comparison_r{args.repeats}.json'
dest.write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k!='question_means'},indent=2))
