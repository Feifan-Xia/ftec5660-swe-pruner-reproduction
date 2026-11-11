"""Audit the completed pilot without changing its evidence or calling an API."""
import collections
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'results/full'
OUT.mkdir(parents=True, exist_ok=True)

def read(p):
    return json.loads(p.read_text(encoding='utf-8'))

ledger = [json.loads(x) for x in (ROOT/'runs/glm/pinned/formal_usage.jsonl').read_text().splitlines()]
parameters = collections.Counter()
systems = collections.Counter()
rows = []
prunes = []
empty_commands = []
for task_path in sorted((ROOT/'runs/glm/pinned/formal').glob('*/q*/attempt*/task.json')):
    task = read(task_path)
    mode, index, repeat, attempt = (task[k] for k in ('mode','index','repeat','attempt'))
    folder = task_path.parent
    session = f'glm-pinned-{mode}-{index}-{repeat}-a{attempt}'
    calls = [x for x in ledger if x['session'] == session]
    for call in calls:
        body = read(ROOT/'runs/glm/pinned/requests'/f"{call['request_id']}.request.json")['body']
        parameters[json.dumps({k:body.get(k) for k in ('temperature','top_p','max_tokens','reasoning','seed')},sort_keys=True)] += 1
        system = [m for m in body['messages'] if m['role']=='system']
        systems[hashlib.sha256(json.dumps(system,sort_keys=True).encode()).hexdigest()] += 1
    traj = read(next((folder/'trajectories').rglob('*.traj.json')))
    observations = [e['observation'] for e in traj['events'] if e.get('type')=='ObservationEvent' and 'observation' in e]
    answers = [json.loads(x) for p in (folder/'answers').rglob('*answers.jsonl') for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
    usage = sum(c.get('usage',{}).get('prompt_tokens',0)+c.get('usage',{}).get('completion_tokens',0) for c in calls)
    actions = [e.get('action',{}) for e in traj['events'] if e.get('type')=='ActionEvent']
    action_by_id = {e.get('id'):e.get('action',{}) for e in traj['events'] if e.get('type')=='ActionEvent'}
    previous_action = None
    for e in traj['events']:
        if e.get('type')=='ActionEvent':
            previous_action = e.get('action')
        if e.get('type')=='ObservationEvent' and e.get('observation',{}).get('output')=='(No output)':
            empty_commands.append({'mode':mode,'index':index,'repeat':repeat,'action':action_by_id.get(e.get('action_id'),previous_action)})
    hinted = [a for a in actions if a.get('context_focus_question')]
    for o in observations:
        if o.get('pruned'):
            prunes.append({'mode':mode,'index':index,'repeat':repeat,'info':o.get('prune_info'), 'raw_chars':len(o.get('original_output') or ''),'output_chars':len(o.get('output') or '')})
    rows.append({'mode':mode,'index':index,'repeat':repeat,'ledger_tokens':usage,'runner_tokens':answers[-1].get('token_cost'),
                 'hinted_actions':len(hinted),'pruned_observations':sum(bool(o.get('pruned')) for o in observations),
                 'no_output':sum(o.get('output')=='(No output)' for o in observations),
                 'error_outputs':[o.get('output','')[:250] for o in observations if str(o.get('output','')).startswith('Error')],
                 'agent_cost':sum(c['cost'] for c in calls)})
result = {'request_parameters':dict(parameters),'system_prompt_hashes':dict(systems),'cells':rows,'prunes':prunes,'empty_commands':empty_commands,
          'runner_ledger_token_mismatches':[r for r in rows if r['ledger_tokens']!=r['runner_tokens']],
          'errors':[r for r in rows if r['error_outputs']],
          'primary_agent_cost':sum(r['agent_cost'] for r in rows),
          'primary_judge_cost':sum(c['cost'] for c in ledger if c['session'].startswith('judge-'))}
(OUT/'prior_audit.json').write_text(json.dumps(result,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if k not in ('cells','prunes')},indent=2))
