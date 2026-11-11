"""Audit retained request bounds against pre-send failures and saved receipts."""
import argparse,json,os
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--apply',action='store_true');args=parser.parse_args()
rows=[json.loads(x) for x in (ROOT/'runs/full/formal_usage.jsonl').read_text().splitlines()]
auth_path=ROOT/'runs/full/budget_authorization.json';auth=json.loads(auth_path.read_text())
already=auth.get('transport_reconciliations',{})
covered=set(auth.get('account_bound_reconciliation',{}).get('covered_request_ids',[]))
for refresh in auth.get('account_bound_refreshes',[]):
    covered.update(refresh['covered_request_ids'])
adjustments=[];unresolved=[]
for row in rows:
    if row.get('cost_kind')!='unreconciled_reserve' or row['request_id'] in already or row['request_id'] in covered:continue
    rid=row['request_id'];p=ROOT/'runs/full/requests'/f'{rid}.response.txt'
    item={'request_id':rid,'session':row['session'],'original_bound':row['cost']}
    if row.get('error')=='ConnectError' and not p.exists():
        item.update(verified_cost=0,basis='HTTPX ConnectError before connection establishment; no HTTP response; retained request has no transmitted API completion.')
    elif p.exists():
        raw=p.read_text(encoding='utf-8',errors='replace');objects=[];invalid=0
        try:objects.append(json.loads(raw))
        except ValueError:
            for line in raw.splitlines():
                if not line.startswith('data:'):continue
                payload=line[5:].strip()
                if payload=='[DONE]':continue
                try:objects.append(json.loads(payload))
                except ValueError:invalid+=1
        receipts=[o for o in objects if isinstance(o,dict) and isinstance(o.get('usage'),dict) and o['usage'].get('cost') is not None]
        if receipts:
            receipt=receipts[-1]
            item.update(verified_cost=receipt['usage']['cost'],usage=receipt['usage'],generation_id=receipt.get('id'),basis='Provider usage receipt recovered from saved response',invalid_sse_lines=invalid)
    if 'verified_cost' in item:
        item['released_bound']=item['original_bound']-item['verified_cost'];adjustments.append(item)
    else:unresolved.append({'request_id':rid,'error':row.get('error'),'status':row.get('status'),'bound':row['cost']})
refund=sum(a['released_bound'] for a in adjustments)
out={'adjustments':adjustments,'unresolved':unresolved,'refund':refund,'ceiling':auth['project_limit_usd']}
if args.apply:
    assert 'external_probe_reserve_usd' not in auth
    auth['prior_stage_conservative_usd']-=refund;auth['meter_limit_usd']+=refund
    auth['transport_reconciliations']={**already,**{a['request_id']:a for a in adjustments}}
    assert abs(auth['prior_stage_conservative_usd']+auth['meter_limit_usd']+auth['margin_usd']-auth['project_limit_usd'])<1e-8
    temp=auth_path.with_suffix('.tmp');temp.write_text(json.dumps(auth,indent=2),encoding='utf-8');os.replace(temp,auth_path)
    target=ROOT/'results/full/transport_reconciliations.json'
    target.write_text(json.dumps({'adjustments':list(auth['transport_reconciliations'].values()),'latest_unresolved':unresolved},indent=2),encoding='utf-8')
else:(ROOT/'results/full/transport_reconciliation_proposal.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out,indent=2))
