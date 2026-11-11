"""Replace settled Go uncached estimates with recorded list costs; retain uncertainty."""
import argparse,hashlib,json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
ledger=ROOT/'runs/api_usage.jsonl'
rows=[json.loads(x) for x in ledger.read_text().splitlines()]
network=[json.loads(x) for x in (ROOT/'runs/network_checks.jsonl').read_text().splitlines()]
initial=.0000297
network_cost=sum(r.get('usage',{}).get('opencode',{}).get('list_cost',0) for r in network)
old=initial+network_cost;new=initial+network_cost;settled=0;unresolved=0;cash=0
for row in rows:
    if row.get('error')=='ConnectError':continue
    bound=row.get('charged_bound_usd',0);old+=bound
    usage=row.get('usage',{});list_cost=usage.get('opencode',{}).get('list_cost')
    if list_cost is not None:
        assert usage.get('opencode',{}).get('billing_source')=='go'
        new+=list_cost;settled+=1;cash+=usage.get('cost',0)
    else:new+=bound;unresolved+=bound
assert abs(old-4.4250627)<1e-6,(old,'Historical carry mismatch')
delta=min(old,4.4250627)-new
result={'old_go_stage_uncached_bound_usd':old,'reconciled_go_stage_usd':new,'released_estimate_usd':delta,
        'settled_usage_rows':settled,'recorded_cash_usd':cash,'retained_unresolved_bounds_usd':unresolved,
        'retained_initial_probe_bound_usd':initial,'network_list_cost_usd':network_cost,
        'ledger_sha256':hashlib.sha256(ledger.read_bytes()).hexdigest(),
        'basis':'User requested actual-usage recalibration. Use provider-recorded list costs for settled Go usage (cash charged zero); preserve missing-usage bounds, initial probe bound and every OpenRouter reservation. USD 12 ceiling stays unchanged.'}
if args.apply:
    p=ROOT/'runs/full/budget_authorization.json';auth=json.loads(p.read_text())
    assert 'go_usage_reconciliation' not in auth,'Already reconciled'
    assert 'external_probe_reserve_usd' not in auth,'Wait for external probe transaction'
    result['authorization_before']=dict(auth)
    auth['prior_stage_conservative_usd']-=delta;auth['meter_limit_usd']+=delta
    auth['go_usage_reconciliation']={k:v for k,v in result.items() if k!='authorization_before'}
    assert abs(auth['prior_stage_conservative_usd']+auth['meter_limit_usd']+auth['margin_usd']-auth['project_limit_usd'])<1e-8
    temp=p.with_suffix('.tmp');temp.write_text(json.dumps(auth,indent=2),encoding='utf-8');os.replace(temp,p)
    result['authorization_after']=auth
(ROOT/'results/full/go_budget_reconciliation.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in result.items() if not k.startswith('authorization')},indent=2))
