"""Remove verified historical OR receipts counted twice by the whole-key bound."""
import hashlib,json,os,sqlite3,time
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parents[1];auth_path=ROOT/'runs/full/budget_authorization.json';auth=json.loads(auth_path.read_text())
assert 'account_bound_reconciliation' in auth and 'historical_overlap_reconciliation' not in auth
provider_id='fbd4c8ff-5c35-476d-9a5c-0b065f897e20'
# All prior OR entrypoints use this same credential source; no key rotation was
# made in this project. Retain every unresolved historical allowance separately.
sources=['revision_glm/proxy.py','revision_glm/judge_pilot.py','revision_glm/meter.py','revision_full/probe_novita.py']
for name in sources:assert provider_id in (ROOT/name).read_text(encoding='utf-8')
ledger_names=['runs/glm/usage.jsonl','runs/glm/judge_usage.jsonl','runs/glm/formal_usage.jsonl','runs/glm/pinned/formal_usage.jsonl']
ledgers=[];known=0;generation_samples=[]
for name in ledger_names:
    path=ROOT/name;rows=[json.loads(x) for x in path.read_text(encoding='utf-8').splitlines()]
    cost=sum(r.get('usage',{}).get('cost',0) or 0 for r in rows);known+=cost
    ledgers.append({'path':name,'known_provider_receipts_usd':cost,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    valid=[r for r in rows if r.get('generation_id') and r.get('usage',{}).get('cost') is not None]
    if valid:generation_samples.append(valid[0])
known+=auth['external_novita_probe_cost_usd']
assert known<auth['account_bound_reconciliation']['historical_conservative_retained_usd']
db=sqlite3.connect('file:'+str(Path.home()/'.cc-switch/cc-switch.db')+'?mode=ro',uri=True)
cfg=json.loads(db.execute('select settings_config from providers where id=?',(provider_id,)).fetchone()[0]);db.close()
headers={'Authorization':'Bearer '+cfg['auth']['OPENAI_API_KEY']};verified=[]
with httpx.Client(trust_env=False,timeout=20) as client:
    for row in generation_samples:
        r=client.get('https://openrouter.ai/api/v1/generation',params={'id':row['generation_id']},headers=headers);r.raise_for_status();data=r.json()['data']
        assert abs(data['total_cost']-row['usage']['cost'])<1e-9
        verified.append({'generation_id':row['generation_id'],'service_total_cost':data['total_cost'],'ledger_cost':row['usage']['cost']})
    r=client.get('https://openrouter.ai/api/v1/key',headers=headers);r.raise_for_status();key_data=r.json()['data']
    assert key_data.get('limit_reset') is None and key_data['usage']>known
evidence={'time':time.time(),'shared_credential_source':provider_id,'entrypoint_sources':sources,'historical_ledger_receipts':ledgers,'novita_receipt_usd':auth['external_novita_probe_cost_usd'],'sample_receipts_reverified':verified,'current_key_lifetime_usage_usd':key_data['usage'],'deduplicated_known_historical_charges_usd':known,'basis':'The earlier aggregate bound added entire lifetime key usage to the entire historical carry. These historical provider-reported charges use the same OR credential and are already included in lifetime usage. Remove only that duplicated known amount; retain all unresolved old allowances and all subsequent request reservations. Approved ceiling stays USD12.'}
auth['prior_stage_conservative_usd']-=known;auth['meter_limit_usd']+=known;auth['historical_overlap_reconciliation']=evidence
assert abs(auth['prior_stage_conservative_usd']+auth['meter_limit_usd']+auth['margin_usd']-12)<1e-8
temp=auth_path.with_suffix('.tmp');temp.write_text(json.dumps(auth,indent=2));os.replace(temp,auth_path)
(ROOT/'results/full/historical_overlap_reconciliation.json').write_text(json.dumps(evidence,indent=2));print(json.dumps(evidence,indent=2))
