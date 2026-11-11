"""Verify first-user payloads for the fixed subset against author trajectories."""
import json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
z=zipfile.ZipFile(ROOT/'runs/author_evidence/swepruner-sweqa-reproduce.zip')
questions=[json.loads(x)['question'] for x in (ROOT/'upstream/downstream_eval/multi_turn/sweqa/questions/streamlink.jsonl').read_text(encoding='utf-8').splitlines()]
indices=json.loads((ROOT/'revision_precision/protocol.json').read_text(encoding='utf-8'))['question_indices']
ledger=[json.loads(x) for x in (ROOT/'runs/full/formal_usage.jsonl').read_text().splitlines()]
rows=[]
def texts(c):
    if isinstance(c,str):return c
    return '\n'.join(x['text'] for x in c if x.get('type')=='text')
for mode,archive in [('baseline','glm'),('pruner','glm-pruner')]:
    ts={t['question']:t for n in z.namelist() if n.startswith(f'traj-full-{archive}/streamlink/') and n.endswith('.traj.json') for t in [json.loads(z.read(n))]}
    for i in indices:
        c=next(c for c in ledger if c['session']==f'glm-precision-{mode}-{i}-0-a0')
        b=json.loads((ROOT/'runs/full/requests'/f"{c['request_id']}.request.json").read_text(encoding='utf-8'))['body']
        current=next(m['content'] for m in b['messages'] if m['role']=='user')
        author=next(e['content'] for e in ts[questions[i]]['events'] if e['type']=='MessageEvent' and e.get('source')=='user')
        rows.append({'index':i,'mode':mode,'equal':texts(current)==texts(author),'current_chars':len(texts(current)),'author_chars':len(texts(author))})
(ROOT/'results/full/user_prompt_audit.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
print('Exact first-user prompt matches:',sum(r['equal'] for r in rows),'/',len(rows))
if not all(r['equal'] for r in rows):print(json.dumps(rows,indent=2))
