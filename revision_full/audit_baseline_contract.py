"""Compare baseline contracts independently of pruner contracts."""
import difflib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
z=zipfile.ZipFile(ROOT/'runs/author_evidence/swepruner-sweqa-reproduce.zip')
t=json.loads(z.read('traj-full-glm/streamlink/streamlink_q1.traj.json'))
s=next(e for e in t['events'] if e['type']=='SystemPromptEvent')
calls=[json.loads(x) for x in (ROOT/'runs/full/formal_usage.jsonl').read_text().splitlines()]
c=next(c for c in calls if c['session'].startswith('glm-precision-baseline-'))
b=json.loads((ROOT/'runs/full/requests'/f"{c['request_id']}.request.json").read_text())['body']
out={}
for name,left,right in [('system',s['system_prompt']['text'],next(m['content'] for m in b['messages'] if m['role']=='system')),('tools',json.dumps(s['tools'],sort_keys=True,indent=2),json.dumps(b['tools'],sort_keys=True,indent=2))]:
    diff='\n'.join(difflib.unified_diff(left.splitlines(),right.splitlines(),fromfile='author',tofile='current',lineterm=''))
    out[name]={'equal':left==right,'diff':diff}
(ROOT/'results/full/baseline_contract.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))
