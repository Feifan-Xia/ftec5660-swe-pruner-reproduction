"""Compare the released trajectories' actual tool contract with our requests."""
import difflib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
z=zipfile.ZipFile(ROOT/'runs/author_evidence/swepruner-sweqa-reproduce.zip')
t=json.loads(z.read('traj-full-glm-pruner/streamlink/streamlink_q1.traj.json'))
print('First events:',[(e['type'],list(e)) for e in t['events'][:4]])
system=next(e for e in t['events'] if e['type']=='SystemPromptEvent')
print('TOOLS',json.dumps(system.get('tools'),ensure_ascii=False,indent=2)[:14000])
print('USER',json.dumps(next(e for e in t['events'] if e['type']=='MessageEvent' and e.get('source')=='user'),ensure_ascii=False)[:5000])
actions=[e.get('action',{}) for e in t['events'] if e['type']=='ActionEvent']
print('FIRST ACTIONS',json.dumps(actions[:5],indent=2,ensure_ascii=False)[:5000])
report={'system':system,'first_user':next(e for e in t['events'] if e['type']=='MessageEvent' and e.get('source')=='user'),'first_actions':actions[:5]}
(ROOT/'runs/author_evidence/pruner_contract.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
ledger=[json.loads(x) for x in (ROOT/'runs/glm/pinned/formal_usage.jsonl').read_text().splitlines()]
request=next(r for r in ledger if r['session'].startswith('glm-pinned-pruner-'))
body=json.loads((ROOT/'runs/glm/pinned/requests'/f"{request['request_id']}.request.json").read_text())['body']
local_system=next(m for m in body['messages'] if m['role']=='system')['content']
import difflib
author_system=system['system_prompt']['text'] if isinstance(system['system_prompt'],dict) else system['system_prompt']
diff='\n'.join(difflib.unified_diff(author_system.splitlines(),local_system.splitlines(),fromfile='authors',tofile='local',lineterm=''))
(ROOT/'results/full/system_prompt_diff.txt').write_text(diff,encoding='utf-8')
print('SYSTEM DIFF',diff[:15000])
author_tool=system['tools'][0]
local_tool=next(t for t in body['tools'] if t['function']['name']=='pruner_bash')
tdiff='\n'.join(difflib.unified_diff(json.dumps(author_tool,indent=2).splitlines(),json.dumps(local_tool,indent=2).splitlines(),fromfile='authors',tofile='local',lineterm=''))
(ROOT/'results/full/tool_schema_diff.txt').write_text(tdiff,encoding='utf-8')
print('TOOL DIFF',tdiff)
print('FIRST OBS',json.dumps(next(e for e in t['events'] if e['type']=='ObservationEvent'),ensure_ascii=False)[:4000])
