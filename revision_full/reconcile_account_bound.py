"""Use an overinclusive whole-key receipt as a bound on the current OR stage.

Historical conservative costs are retained in full. Adding the key's entire
lifetime usage double-counts historical OR activity, providing a conservative
ceiling without assigning zero cost to individual post-send failures.
"""
import json,sqlite3,os,time,hashlib
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parents[1];folder=ROOT/'runs/full'
auth_path=folder/'budget_authorization.json';auth=json.loads(auth_path.read_text())
assert 'account_bound_reconciliation' not in auth
health=httpx.get('http://127.0.0.1:8879/health',trust_env=False).json()
assert abs(health['reserved'])<1e-8
db=sqlite3.connect('file:'+str(Path.home()/'.cc-switch/cc-switch.db')+'?mode=ro',uri=True)
cfg=json.loads(db.execute('select settings_config from providers where id=?',('fbd4c8ff-5c35-476d-9a5c-0b065f897e20',)).fetchone()[0]);db.close()
with httpx.Client(trust_env=False,timeout=20) as c:
    r=c.get('https://openrouter.ai/api/v1/key',headers={'Authorization':'Bearer '+cfg['auth']['OPENAI_API_KEY']});r.raise_for_status();data=r.json()['data']
receipt={k:data[k] for k in ['usage','usage_daily','usage_weekly','usage_monthly','byok_usage','limit_reset'] if k in data}
assert receipt.get('byok_usage',0)==0
assert receipt.get('limit_reset') is None
rows=[json.loads(x) for x in (folder/'formal_usage.jsonl').read_text().splitlines()]
assert time.time()-max(r['time']+r['seconds'] for r in rows)>60,'Wait for settlement while no requests are running'
known=sum(r.get('usage',{}).get('cost',0) or 0 for r in rows)
assert data['usage']>=known
prior=json.loads((ROOT/'results/full/go_budget_reconciliation.json').read_text())['authorization_after']['prior_stage_conservative_usd']
gross=sum(r['cost'] for r in rows);old=auth['prior_stage_conservative_usd']+gross
target=prior+data['usage']
assert target<old and target<auth['project_limit_usd']
evidence={'time':time.time(),'receipt':receipt,'historical_conservative_retained_usd':prior,'whole_key_lifetime_usage_usd':data['usage'],'current_stage_known_receipts_usd':known,'before_project_bound_usd':old,'after_project_bound_usd':target,'released_bound_usd':old-target,'ledger_sha256':hashlib.sha256((folder/'formal_usage.jsonl').read_bytes()).hexdigest(),'covered_request_ids':[r['request_id'] for r in rows],'basis':__doc__,'source':'https://openrouter.ai/docs/api/api-reference/api-keys/get-current-api-key'}
auth['prior_stage_conservative_usd']-=old-target;auth['meter_limit_usd']+=old-target;auth['account_bound_reconciliation']=evidence
assert abs(auth['prior_stage_conservative_usd']+auth['meter_limit_usd']+auth['margin_usd']-12)<1e-8
temp=auth_path.with_suffix('.tmp');temp.write_text(json.dumps(auth,indent=2));os.replace(temp,auth_path)
(ROOT/'results/full/account_bound_reconciliation.json').write_text(json.dumps(evidence,indent=2))
print(json.dumps({k:v for k,v in evidence.items() if k!='covered_request_ids'},indent=2))
