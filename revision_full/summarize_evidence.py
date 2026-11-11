"""One traceable numerical source for the revised manuscript's comparisons."""
import json,random,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def mean(xs):return statistics.mean(xs)
def group(stage,mode,corrected=False):
    p=ROOT/f'results/{stage}/cells.json'
    overlay=p.with_name('terminal_corrected_cells.json')
    if corrected and overlay.exists():p=overlay
    cells=[r for r in read(p) if r['mode']==mode]
    assert all(r['qualified'] and r['score'] is not None for r in cells)
    return cells
def aggregate(rows):
    return dict(n=len(rows),questions=len({r['index'] for r in rows}),
        score=mean(r['score'] for r in rows),tokens=mean(r['total_tokens'] for r in rows),
        requests=mean(r['api_requests'] for r in rows),rounds=mean(r['author_rounds'] for r in rows),
        seconds=mean(r['seconds'] for r in rows),
        pruning_task_percent=100*sum(r['prune_calls']>0 for r in rows)/len(rows),
        expand_task_percent=100*sum(r['expand_calls']>0 for r in rows)/len(rows),
        prune_calls=sum(r['prune_calls'] for r in rows),expand_calls=sum(r['expand_calls'] for r in rows),
        raw=sum(r['raw_pruned_tokens'] for r in rows),kept=sum(r['kept_pruned_tokens'] for r in rows),
        selected_agent_usd=sum(r['cost'] for r in rows),
        first_attempt_percent=100*sum(r['attempt']==0 for r in rows)/len(rows),
        execution_complete_percent=100*sum(r['qualified'] and r['answered'] for r in rows)/len(rows))
def compare(control,treatment):
    assert {(r['index'],r['repeat']) for r in control}=={(r['index'],r['repeat']) for r in treatment}
    indices=read(ROOT/'revision_precision/protocol.json')['question_indices'];effects={}
    assert set(indices)=={r['index'] for r in control}
    for metric in ['score','total_tokens','api_requests']:
        byq=[{i:mean(r[metric] for r in rows if r['index']==i) for i in indices} for rows in [control,treatment]]
        rng=random.Random(5660);samples=[]
        for _ in range(10000):
            pick=rng.choices(indices,k=len(indices));b,t=[mean(g[i] for i in pick) for g in byq];samples.append(100*(t/b-1))
        samples.sort();b,t=[mean(g.values()) for g in byq]
        effects[metric]={'relative_percent':100*(t/b-1),'ci95_percent':[samples[249],samples[9749]]}
    return effects

groups={'original_full':group('precision','baseline'),'original_pruner':group('precision','pruner'),
    'repaired_full':group('precision','baseline',True),'required_full':group('hintfull','pruner'),
    'required_pruner':group('hint','pruner'),'required_pruner_repaired':group('hint','pruner',True),
    'required_recovery':group('recovery','recovery')}
comparisons={'original':('original_full','original_pruner'),'terminal_repaired':('repaired_full','original_pruner'),
    'activation_raw':('required_full','required_pruner'),'activation_repaired':('required_full','required_pruner_repaired'),
    'required_recovery_raw':('required_pruner','required_recovery'),'required_recovery_repaired':('required_pruner_repaired','required_recovery')}
optional=ROOT/'results/optional/cells.json'
if optional.exists() and len(read(optional))==24:
    groups['optional_recovery']=group('optional','recovery');comparisons['optional_recovery']=('original_pruner','optional_recovery')
out={'groups':{k:aggregate(v) for k,v in groups.items()},'comparisons':{k:compare(groups[b],groups[t]) for k,(b,t) in comparisons.items()},
     'comparison_groups':comparisons,'source_paths':sorted({r['path'] for rows in groups.values() for r in rows}),
     'scope':'All planned cells in each complete study. Repaired full and required-pruner groups replace only affected terminal-summary branches on identical fixed agent prefixes; raw results remain separate. Optional recovery is a later independent stage.'}
(ROOT/'results/full/manuscript_evidence.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps({'groups':out['groups'],'comparisons':out['comparisons']},indent=2))
