"""Test an isolated schema constraint on the same frozen first-request fixtures."""
import concurrent.futures,copy,json,zipfile
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parents[1]
z=zipfile.ZipFile(ROOT/'runs/author_evidence/swepruner-sweqa-reproduce.zip')
questions=[json.loads(x)['question'] for x in (ROOT/'upstream/downstream_eval/multi_turn/sweqa/questions/streamlink.jsonl').read_text(encoding='utf-8').splitlines()]
ts={t['question']:t for n in z.namelist() if n.startswith('traj-full-glm-pruner/streamlink/') and n.endswith('.traj.json') for t in [json.loads(z.read(n))]}
folder=ROOT/'runs/full/diagnostics/required_hint';folder.mkdir(parents=True,exist_ok=True)
protocol={'indices':[43,26,17],'intervention':'Require a nonempty context_focus_question in the pruner_bash schema; every other schema and prompt string remains unchanged.','tool_execution':False,'interpretation':'Mechanism diagnostic; the released paper schema keeps this field optional.'}
(folder/'protocol.json').write_text(json.dumps(protocol,indent=2),encoding='utf-8')
def run(index):
    target=folder/f'q{index}.json'
    if target.exists():return json.loads(target.read_text(encoding='utf-8'))
    t=ts[questions[index]];system=next(e for e in t['events'] if e['type']=='SystemPromptEvent');tools=copy.deepcopy(system['tools'])
    parameters=tools[0]['function']['parameters'];parameters['required'].append('context_focus_question');parameters['properties']['context_focus_question']['minLength']=1
    user=next(e for e in t['events'] if e['type']=='MessageEvent' and e.get('source')=='user')['content']
    body={'model':'z-ai/glm-4.6','temperature':0,'top_p':1,'messages':[{'role':'system','content':system['system_prompt']['text']},{'role':'user','content':user}],'tools':tools}
    r=httpx.post('http://127.0.0.1:8879/v1/chat/completions',trust_env=False,timeout=260,headers={'x-opencode-session':f'required-hint-{index}'},json=body);r.raise_for_status();raw=r.json()
    (folder/f'q{index}-raw.json').write_text(json.dumps(raw,indent=2),encoding='utf-8')
    calls=[{'name':c['function']['name'],'arguments':json.loads(c['function']['arguments'])} for c in raw['choices'][0]['message'].get('tool_calls',[])]
    row={'index':index,'tools':calls,'has_hint':any(c['arguments'].get('context_focus_question') for c in calls),'cost':raw.get('usage',{}).get('cost')}
    target.write_text(json.dumps(row,indent=2),encoding='utf-8');print(json.dumps(row),flush=True);return row
with concurrent.futures.ThreadPoolExecutor(3) as pool:rows=list(pool.map(run,protocol['indices']))
(ROOT/'results/full/required_hint_probe.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
