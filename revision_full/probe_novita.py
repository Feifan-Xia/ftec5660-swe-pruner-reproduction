"""Three fixed first-action probes on the advertised BF16 route, within the same budget."""
import json,os,sqlite3,time,uuid,zipfile
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'runs/full/diagnostics/novita';folder.mkdir(parents=True,exist_ok=True)
assert not (folder/'summary.json').exists(),'Preserve this single diagnostic block'
auth_path=ROOT/'runs/full/budget_authorization.json'
auth=json.loads(auth_path.read_text());original=dict(auth)
external_cap=.35
health=httpx.get('http://127.0.0.1:8879/health',trust_env=False).json()
assert health['spent']+health['reserved']+external_cap<auth['meter_limit_usd']
def authorize(data):
    temp=auth_path.with_suffix('.tmp');temp.write_text(json.dumps(data,indent=2),encoding='utf-8');os.replace(temp,auth_path)
auth['meter_limit_usd']-=external_cap;auth['prior_stage_conservative_usd']+=external_cap
auth['external_probe_reserve_usd']=external_cap
authorize(auth)
db=sqlite3.connect('file:'+str(Path.home()/'.cc-switch/cc-switch.db')+'?mode=ro',uri=True)
cfg=json.loads(db.execute('select settings_config from providers where id=?',('fbd4c8ff-5c35-476d-9a5c-0b065f897e20',)).fetchone()[0]);db.close()
client=httpx.Client(trust_env=False,timeout=240)
z=zipfile.ZipFile(ROOT/'runs/author_evidence/swepruner-sweqa-reproduce.zip')
qs=[json.loads(x)['question'] for x in (ROOT/'upstream/downstream_eval/multi_turn/sweqa/questions/streamlink.jsonl').read_text(encoding='utf-8').splitlines()]
ts={t['question']:t for n in z.namelist() if n.startswith('traj-full-glm-pruner/streamlink/') and n.endswith('.traj.json') for t in [json.loads(z.read(n))]}
protocol={'indices':[43,26,17],'intervention':'Accessible BF16 Novita endpoint, same original optional tool contract; diagnostic first actions only, no shell execution.','provider':{'only':['novita'],'allow_fallbacks':False},'temporary_budget_reservation':external_cap}
(folder/'protocol.json').write_text(json.dumps(protocol,indent=2),encoding='utf-8')
records=[];spent=0
try:
    for index in protocol['indices']:
        t=ts[qs[index]];s=next(e for e in t['events'] if e['type']=='SystemPromptEvent')
        u=next(e for e in t['events'] if e['type']=='MessageEvent' and e.get('source')=='user')['content']
        body={'model':'z-ai/glm-4.6','temperature':0,'top_p':1,'max_tokens':16384,'provider':protocol['provider'],'messages':[{'role':'system','content':s['system_prompt']['text']},{'role':'user','content':u}],'tools':s['tools']}
        reserve=2*((len(json.dumps(body).encode())+4096)*.00000055+16384*.0000022)
        assert spent+reserve<=external_cap
        (folder/f'q{index}.request.json').write_text(json.dumps(body),encoding='utf-8')
        row={'index':index,'reserve':reserve,'started':time.time()}
        try:
            r=client.post('https://openrouter.ai/api/v1/chat/completions',headers={'Authorization':'Bearer '+cfg['auth']['OPENAI_API_KEY']},json=body)
            (folder/f'q{index}.response.txt').write_bytes(r.content)
            payload=r.json();cost=payload.get('usage',{}).get('cost')
            row.update(status=r.status_code,cost=cost if cost is not None else reserve,cost_kind='provider_reported' if cost is not None else 'unreconciled_reserve',provider=payload.get('provider'),generation_id=payload.get('id'))
            calls=[{'name':c['function']['name'],'arguments':json.loads(c['function']['arguments'])} for c in payload.get('choices',[{}])[0].get('message',{}).get('tool_calls',[])]
            row.update(tools=calls,has_hint=any(c['arguments'].get('context_focus_question') for c in calls))
        except Exception as exc:
            row.update(error=type(exc).__name__,cost=reserve,cost_kind='unreconciled_reserve')
        spent+=row['cost'];records.append(row)
        (folder/f'q{index}.json').write_text(json.dumps(row,indent=2),encoding='utf-8')
        print(json.dumps({k:v for k,v in row.items() if k!='tools'}),flush=True)
finally:
    original['prior_stage_conservative_usd']+=spent;original['meter_limit_usd']-=spent
    original['external_novita_probe_cost_usd']=spent
    authorize(original)
    out={'protocol':protocol,'rows':records,'total_cost':spent}
    (folder/'summary.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
    (ROOT/'results/full/novita_hint_probe.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
