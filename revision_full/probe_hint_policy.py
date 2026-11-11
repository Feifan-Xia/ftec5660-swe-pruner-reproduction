"""Isolate model request policy from filesystem effects using author first prompts."""
import concurrent.futures,json,time,zipfile
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parents[1]
z=zipfile.ZipFile(ROOT/'runs/author_evidence/swepruner-sweqa-reproduce.zip')
questions=[json.loads(x)['question'] for x in (ROOT/'upstream/downstream_eval/multi_turn/sweqa/questions/streamlink.jsonl').read_text(encoding='utf-8').splitlines()]
trajectories={t['question']:t for n in z.namelist() if n.startswith('traj-full-glm-pruner/streamlink/') and n.endswith('.traj.json') for t in [json.loads(z.read(n))]}
folder=ROOT/'runs/full/diagnostics/hint_policy';folder.mkdir(parents=True,exist_ok=True)
protocol={'indices':[43,26,17],'variants':['default','enabled','disabled'],'temperature':0,'top_p':1,'tool_execution':False,
          'scope':'First-request diagnostic on predeclared development questions. Compare hint generation on the exact published prompt/schema before any filesystem observations. Original gateway reasoning setting is unknown.'}
plan=folder/'protocol.json'
if plan.exists():assert json.loads(plan.read_text())==protocol
else:plan.write_text(json.dumps(protocol,indent=2),encoding='utf-8')
def run(index,variant):
    target=folder/f'q{index}-{variant}.json'
    if target.exists():return json.loads(target.read_text(encoding='utf-8'))
    t=trajectories[questions[index]];system=next(e for e in t['events'] if e['type']=='SystemPromptEvent')
    text=system['system_prompt']['text']
    user=next(e for e in t['events'] if e['type']=='MessageEvent' and e.get('source')=='user')['content']
    body={'model':'z-ai/glm-4.6','temperature':0,'top_p':1,'messages':[{'role':'system','content':text},{'role':'user','content':user}], 'tools':system['tools']}
    if variant!='default':body['reasoning']={'enabled':variant=='enabled'}
    response=httpx.post('http://127.0.0.1:8879/v1/chat/completions',trust_env=False,timeout=260,
                        headers={'x-opencode-session':f'hint-policy-{index}-{variant}'},json=body)
    response.raise_for_status();raw=response.json()
    (folder/f'q{index}-{variant}-raw.json').write_text(json.dumps(raw,indent=2),encoding='utf-8')
    calls=raw['choices'][0]['message'].get('tool_calls',[])
    details=[{'name':c['function']['name'],'arguments':json.loads(c['function']['arguments'])} for c in calls]
    row={'index':index,'variant':variant,'tools':details,'has_hint':any(c['arguments'].get('context_focus_question') for c in details),
         'reasoning_tokens':raw.get('usage',{}).get('completion_tokens_details',{}).get('reasoning_tokens'),'cost':raw.get('usage',{}).get('cost')}
    target.write_text(json.dumps(row,indent=2),encoding='utf-8');print(json.dumps(row),flush=True);return row
with concurrent.futures.ThreadPoolExecutor(3) as pool:
    jobs=[pool.submit(run,i,v) for i in protocol['indices'] for v in protocol['variants']]
    rows=[f.result() for f in jobs]
(ROOT/'results/full/hint_policy_probe.json').write_text(json.dumps(rows,indent=2),encoding='utf-8')
