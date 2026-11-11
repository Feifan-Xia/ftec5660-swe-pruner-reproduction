"""Replay only the final summary on an identical saved agent trajectory.

Original runs remain untouched. Repaired requests preserve the released summary
system/user template, model and temperature0.3; tool evidence is the only change.
"""
import argparse,copy,hashlib,json,re,sys,time
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from score_results import official_prompt,DIMENSIONS
OUT=ROOT/'runs/full/terminal_repair';OUT.mkdir(parents=True,exist_ok=True)
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,d):p.write_text(json.dumps(d,indent=2,ensure_ascii=False),encoding='utf-8')
def text_content(value):
    if isinstance(value,str):return value
    return '\n'.join(x['text'] for x in value if x.get('type')=='text')
def visible_saved(o,task,store):
    if not o.get('pruned'):return o.get('content') or o.get('output') or o.get('message') or ''
    kept=o['output'];raw=o['original_output']
    prefix='All outputs are judged relevant. Raw output: \n' if kept==raw else 'Filtered some outputs, good try! Pruned output: \n'
    value=prefix+kept
    if task['mode']=='recovery':
        key='obs_'+hashlib.sha256(raw.encode()).hexdigest()[:16];assert store['observations'][key]==raw
        value+=f'\n\n\nOriginal output saved as {key}, {len(raw.splitlines())} lines. Use the expand tool with inclusive one-based start/end lines to recover details.'
    return value
def prepare():
    ledger=[json.loads(x) for x in (ROOT/'runs/full/formal_usage.jsonl').read_text(encoding='utf-8').splitlines()]
    plans=[]
    for stage in ['precision','hint','hintfull','recovery']:
        for selection in sorted((ROOT/f'runs/{stage}/formal').glob('*/q*/selection.json')):
            a=read(selection).get('selected_attempt')
            if a is None:continue
            folder=selection.parent/f'attempt{a}'
            if not read(folder/'qualification.json')['qualified']:continue
            task=read(folder/'task.json');session=f"glm-{stage}-{task['mode']}-{task['index']}-{task['repeat']}-a{a}"
            calls=[r for r in ledger if r['session']==session];summary=[r for r in calls if r.get('parameters',{}).get('temperature')==.3 and r.get('usage')]
            if not summary:continue
            assert len(summary)==1,'Diagnose multiple final-summary receipts'
            original=summary[0];old_body=read(ROOT/'runs/full/requests'/f"{original['request_id']}.request.json")['body']
            trajectory=read(next((folder/'trajectories/streamlink').glob('*.traj.json')))
            observations=[e['observation'] for e in trajectory['events'] if e['type']=='ObservationEvent']
            store=read(folder/'observations.json') if (folder/'observations.json').exists() else {}
            visible=[visible_saved(o,task,store) for o in observations]
            native=[r for r in calls if r.get('parameters',{}).get('temperature')!=.3]
            last=max(native,key=lambda r:r['time']);wire=read(ROOT/'runs/full/requests'/f"{last['request_id']}.request.json")['body']
            tool_text=[text_content(m['content']) for m in wire['messages'] if m['role']=='tool']
            assert tool_text==visible[:len(tool_text)],'Saved display differs from actual agent wire messages'
            body=copy.deepcopy(old_body);prompt=body['messages'][1]['content']
            pattern=re.compile(r'(Tool Output: Observation: )(.+?)(?=\n\n(?:Assistant:|User:|Tool Output:|Based on the conversation history above)|\Z)',re.S)
            matches=list(pattern.finditer(prompt));assert len(matches)==len(visible)
            parts=[];pos=0
            for match,value in zip(matches,visible):parts.extend([prompt[pos:match.start()],match[1]+value]);pos=match.end()
            parts.append(prompt[pos:]);body['messages'][1]['content']=''.join(parts)
            name=f"{stage}-{task['mode']}-q{task['index']}-r{task['repeat']}-a{a}";dest=OUT/name;dest.mkdir(exist_ok=True)
            plan={'stage':stage,'task':task,'original_path':folder.relative_to(ROOT).as_posix(),'original_terminal_request':original,'wire_tool_messages_verified':len(tool_text),'observations_restored':len(visible),'empty_observations_before':sum(m[2]=='[]' for m in matches),'original_prompt_chars':len(prompt),'repaired_prompt_chars':len(body['messages'][1]['content']),'body':body,'change':'Replace terminal-summary observation serialization with the exact agent-visible display. Preserve every other request field and the entire preceding trajectory.'}
            if (dest/'plan.json').exists():assert read(dest/'plan.json')==plan
            else:write(dest/'plan.json',plan)
            plans.append(dest)
    return plans
def call(body,session,dest,kind):
    for n in range(3):
        path=dest/f'{kind}_{n}.json';failure=dest/f'{kind}_{n}.failure.json'
        if path.exists():return read(path)
        if failure.exists():continue
        r=httpx.post('http://127.0.0.1:8879/v1/chat/completions',json=body,headers={'x-opencode-session':session+f'-{kind}{n}'},trust_env=False,timeout=260)
        if r.status_code!=200:
            write(failure,{'time':time.time(),'status':r.status_code,'body':r.text});r.raise_for_status()
        payload=r.json();assert payload.get('usage') and payload.get('choices');write(path,payload);return payload
    raise RuntimeError('Bounded terminal replay attempts exhausted')
def execute(dest):
    if (dest/'result.json').exists():return
    plan=read(dest/'plan.json');task=plan['task'];session='terminal-repair-'+dest.name
    response=call(plan['body'],session,dest,'summary');answer=response['choices'][0]['message']['content'];assert answer.strip()
    qs=[json.loads(x) for x in (ROOT/'upstream/downstream_eval/multi_turn/sweqa/questions/streamlink.jsonl').read_text(encoding='utf-8').splitlines()];row=qs[task['index']]
    prompt=official_prompt(row['question'],row.get('ground_truth') or row['answer'],answer)
    judge=call({'model':'openai/gpt-5','max_tokens':4096,'reasoning':{'effort':'low'},'messages':[{'role':'user','content':prompt}]},session,dest,'judge')
    scores=json.loads(judge['choices'][0]['message']['content'].strip().removeprefix('```json').removesuffix('```'));assert all(type(scores.get(k)) is int and 1<=scores[k]<=10 for k in DIMENSIONS)
    write(dest/'result.json',{'stage':plan['stage'],'task':task,'original_path':plan['original_path'],'answer':answer,'scores':scores,'mean_score':sum(scores[k] for k in DIMENSIONS)/5,'old_terminal_usage':plan['original_terminal_request']['usage'],'new_terminal_usage':response['usage'],'judge_usage':judge['usage'],'scope':'Fixed-trajectory terminal-summary repair; original agent prefix and old answer retained.'})
    print('Completed terminal repair',dest.name,flush=True)
if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--run',action='store_true');args=parser.parse_args()
    plans=prepare();print('Verified terminal replay plans',len(plans),flush=True)
    if args.run:
        for dest in plans:execute(dest)
