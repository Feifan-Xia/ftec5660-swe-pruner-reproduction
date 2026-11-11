"""Verify complete fixed-question blocks, retries, immutable sources and budget."""
import argparse,hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--study',choices=['precision','hint','hintfull','recovery'],required=True);parser.add_argument('--repeats',type=int,choices=[1,3],required=True);parser.add_argument('--partial',action='store_true');args=parser.parse_args()
def read(p):return json.loads(p.read_text(encoding='utf-8'))
base=ROOT/f'runs/{args.study}/formal';protocol=read(ROOT/f'revision_{args.study}/protocol.json')
manifest=read(base/'runtime_manifest.json');errors=[];pending=[];rows=[]
for name,expected in manifest['files'].items():
    data=(ROOT/name).read_bytes()
    assert hashlib.sha256(data).hexdigest()==expected,f'Frozen source changed: {name}'
qs=[json.loads(x) for x in (ROOT/'upstream/downstream_eval/multi_turn/sweqa/questions/streamlink.jsonl').read_text(encoding='utf-8').splitlines()]
modes=protocol['conditions']
for i in protocol['question_indices']:
    for repeat in range(args.repeats):
        for mode in modes:
            cell=base/mode/f'q{i}_r{repeat}';selection=cell/'selection.json'
            attempts=list(cell.glob('attempt*/task.json'))
            for task_file in attempts:
                d=task_file.parent;task=read(task_file)
                assert (task['index'],task['repeat'],task['mode'])==(i,repeat,mode)
                exposed=[json.loads(x) for x in (d/'questions/streamlink.jsonl').read_text(encoding='utf-8').splitlines()]
                assert exposed==[{'question':qs[i]['question']}]
                assert task['attempt'] in [0,1,2,3]
                if task['attempt']>=2:
                    assert (base/'transport_recovery_v2.json').exists()
                    if task['attempt']==3:assert (base/'transport_recovery_v3.json').exists()
                    for a in range(task['attempt']):assert read(cell/f'attempt{a}/qualification.json')['reasons']==['budget_guard_interruption']
            if not selection.exists() or read(selection)['selected_attempt'] is None:
                pending.append([i,repeat,mode]);continue
            selected=read(selection)['selected_attempt'];out=cell/f'attempt{selected}'
            assert read(out/'qualification.json')['qualified']
            assert read(out/'exit.json')['returncode']==0
            scores=read(out/'score.json');assert abs(sum(scores['scores'].values())/5-scores['mean'])<1e-9
            answers=[json.loads(x) for f in (out/'answers').rglob('*answers.jsonl') for x in f.read_text(encoding='utf-8').splitlines() if x.strip()]
            assert answers[-1]['answer'].strip() and answers[-1]['answer']!='No answer found'
            for a in range(selected):
                old=read(cell/f'attempt{a}/qualification.json');assert not old['qualified']
                assert set(old['reasons'])<={'budget_guard_interruption','process_failure','missing_answer','pruning_service_failure'}
            rows.append({'index':i,'repeat':repeat,'mode':mode,'selected_attempt':selected,'attempts':len(attempts),'score':scores['mean']})
auth=read(ROOT/'runs/full/budget_authorization.json')
ledger=[json.loads(x) for x in (ROOT/'runs/full/formal_usage.jsonl').read_text().splitlines()]
spent=auth['prior_stage_conservative_usd']+sum(r['cost'] for r in ledger)
assert spent<=auth['project_limit_usd']+1e-8
out={'study':args.study,'repeats':args.repeats,'planned':len(protocol['question_indices'])*len(modes)*args.repeats,'complete':len(rows),'pending':pending,'errors':errors,
     'frozen_source_files_verified':len(manifest['files']),'first_agent_attempt_percent':100*sum(r['selected_attempt']==0 for r in rows)/len(rows) if rows else None,
     'retries':[r for r in rows if r['selected_attempt']>0],'project_conservative_usd':spent,'ceiling_usd':auth['project_limit_usd'],
     'recovery_wrapper_sha256':hashlib.sha256((ROOT/'revision_full/resume_subset.py').read_bytes()).hexdigest(),
     'scope':'Frozen runtime hashes, fixed question-only inputs, selected-answer existence, score arithmetic, bounded infrastructure retry provenance and reconciled budget. Failed prior attempts remain in their original directories.'}
(ROOT/f'results/{args.study}/audit_r{args.repeats}.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))
if pending and not args.partial:raise SystemExit('Complete every paired cell before final reporting')
