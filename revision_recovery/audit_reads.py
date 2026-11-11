"""Verify exact line reads and track newly exposed text through each trajectory."""
import argparse,hashlib,json,re
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
parser=argparse.ArgumentParser();parser.add_argument('--study',choices=['recovery','optional'],default='recovery');args=parser.parse_args()
protocol=read(ROOT/f'revision_{args.study}/protocol.json')
cells=read(ROOT/f'results/{args.study}/cells.json');assert len(cells)==protocol['planned_cells'] and all(r['qualified'] and r['score'] is not None for r in cells)
records=[];total_reads=0;stored=0
for cell in cells:
    out=ROOT/cell['path'];store=read(out/'observations.json');observations=store['observations'];seen_positions=set()
    for key,text in observations.items():assert key=='obs_'+hashlib.sha256(text.encode()).hexdigest()[:16]
    for row in store['reads']:
        key,start,end=row['observation_id'],row['start'],row['end'];lines=observations[key].splitlines(keepends=True)
        assert 1<=start<=end<=len(lines) and end-start+1<=200
        assert row['returned_chars']==len(''.join(lines[start-1:end]))
        positions={(key,i) for i in range(start,end+1)}
        assert row['repeated_lines']==len(positions & seen_positions);seen_positions.update(positions)
    stored+=len(observations);total_reads+=len(store['reads'])
    pending=list(store['reads']);visible={}
    for p in (out/'trajectories/streamlink').glob('*.traj.json'):
        for e in read(p)['events']:
            o=e.get('observation',{})
            if o.get('pruned') and 'original_output' in o:
                key='obs_'+hashlib.sha256(o['original_output'].encode()).hexdigest()[:16]
                visible.setdefault(key,set()).update(line.strip() for line in o['output'].splitlines())
            elif isinstance(o.get('content'),str):
                saved=re.search(r'\n\n\nOriginal output saved as (obs_[0-9a-f]{16}), \d+ lines\.',o['content'])
                if saved:
                    key=saved[1];raw=observations[key]
                    assert raw in o['content'][:saved.start()],'Full initial observation is incomplete'
                    visible.setdefault(key,set()).update(line.strip() for line in raw.splitlines())
            a=e.get('action',{})
            if a.get('kind')!='ExpandAction':continue
            key,start,end=a['observation_id'],a['start'],a['end']
            match=next((r for r in pending if (r['observation_id'],r['start'],r['end'])==(key,start,end)),None)
            if match is None:continue
            pending.remove(match)
            returned=[line.strip() for line in observations[key].splitlines()[start-1:end]]
            nonblank=[line for line in returned if (line.split('\t',1)[1] if re.match(r'^\d+\t',line) else line).strip()]
            before=visible.get(key);novel=[line for line in nonblank if before is not None and line not in before]
            records.append({'index':cell['index'],'repeat':cell['repeat'],**match,'prior_pruned_display_found':before is not None,'new_nonblank_lines':len(novel) if before is not None else None,'new_line_examples':novel[:4]})
            visible.setdefault(key,set()).update(returned)
    assert not pending,'Every successful read must match a recorded tool action'
result={'pass':True,'cells':len(cells),'stored_observations':stored,'successful_reads':total_reads,'reads_exposing_new_nonblank_lines':sum((r['new_nonblank_lines'] or 0)>0 for r in records),'unmatched_initial_displays':sum(not r['prior_pruned_display_found'] for r in records),'reads':records,'scope':'Character-exact bounded reads, hash identity, overlap counts and chronological new visible text. Initial visibility includes both full and pruned observations. Text exposure does not establish causal use in the final answer.'}
(ROOT/f'results/{args.study}/recovery_trace_analysis.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k!='reads'},indent=2))
