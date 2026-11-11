"""Apply audited terminal-only overlays while retaining original study cells."""
import copy,json,random,statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
records=[];overlays={}
for path in (ROOT/'runs/full/terminal_repair').glob('*/result.json'):
    r=read(path);plan=read(path.parent/'plan.json');stage=r['stage'];task=r['task']
    if stage not in overlays:overlays[stage]=copy.deepcopy(read(ROOT/f'results/{stage}/cells.json'))
    cell=next(c for c in overlays[stage] if c['path']==r['original_path'])
    before={k:cell[k] for k in ['score','total_tokens','input_tokens','output_tokens','cost']}
    old,new=r['old_terminal_usage'],r['new_terminal_usage']
    for metric,api in [('input_tokens','prompt_tokens'),('output_tokens','completion_tokens'),('total_tokens','total_tokens')]:cell[metric]+=new[api]-old[api]
    cell['cost']+=new['cost']-old['cost'];cell['score']=r['mean_score'];cell['dimensions']=r['scores'];cell['author_filtered_eligible']=all(v!=1 for v in r['scores'].values());cell['terminal_repair']=path.relative_to(ROOT).as_posix()
    records.append({'stage':stage,'index':task['index'],'repeat':task['repeat'],'mode':task['mode'],'before':before,'after':{k:cell[k] for k in before},'score_relative_percent':100*(cell['score']/before['score']-1),'whole_task_tokens_relative_percent':100*(cell['total_tokens']/before['total_tokens']-1),'wire_tool_messages_verified':plan['wire_tool_messages_verified'],'observations_restored':plan['observations_restored']})
for stage,cells in overlays.items():(ROOT/f'results/{stage}/terminal_corrected_cells.json').write_text(json.dumps(cells,indent=2),encoding='utf-8')
summary={'scope':'Counterfactual terminal branch on identical completed agent prefixes. Subtract original terminal usage and add repaired terminal usage; preserve full prior attempts and both terminal branches for actual billing. No tasks or scores selected by outcome.','repairs':records}
if 'precision' in overlays:
    cells=overlays['precision'];assert len(cells)==48 and all(c['qualified'] and c['score'] is not None for c in cells)
    indices=read(ROOT/'revision_precision/protocol.json')['question_indices'];effects={}
    for metric in ['score','total_tokens']:
        byq={m:{i:statistics.mean(c[metric] for c in cells if c['mode']==m and c['index']==i) for i in indices} for m in ['baseline','pruner']}
        means={m:statistics.mean(v.values()) for m,v in byq.items()};rng=random.Random(5660);samples=[]
        for _ in range(10000):
            picked=rng.choices(indices,k=8);b=statistics.mean(byq['baseline'][i] for i in picked);p=statistics.mean(byq['pruner'][i] for i in picked);samples.append(100*(p/b-1))
        samples.sort();effects[metric]={**means,'relative_percent':100*(means['pruner']/means['baseline']-1),'cluster_bootstrap_ci95_percent':[samples[249],samples[9749]]}
    summary['precision_corrected_effects']=effects
(ROOT/'results/full/terminal_repair_analysis.json').write_text(json.dumps(summary,indent=2),encoding='utf-8');print(json.dumps(summary,indent=2))
