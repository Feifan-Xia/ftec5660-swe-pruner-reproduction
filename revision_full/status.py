"""Compact status, budget and pending cells, independent of worker console output."""
import argparse,collections,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'runs/full'
parser=argparse.ArgumentParser();parser.add_argument('--study',choices=['full','subset','precision','hint','hintfull','recovery'],default='full');args=parser.parse_args()
study=ROOT/f'runs/{args.study}'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
ledger=folder/'formal_usage.jsonl'
calls=[json.loads(x) for x in ledger.read_text(encoding='utf-8').splitlines()] if ledger.exists() else []
authorization=read(folder/'budget_authorization.json')
selected=list((study/'formal').glob('*/q*/selection.json'))
tasks=list((study/'formal').glob('*/q*/attempt*/task.json'))
done=collections.Counter(p.parts[-3] for p in selected if read(p).get('selected_attempt') is not None)
running=[{'cell':'/'.join(p.parts[-4:-1]),'seconds':round(time.time()-read(p)['started'])} for p in tasks if not (p.parent/'exit.json').exists()]
failed=[{'cell':'/'.join(p.parts[-4:-1]),'reasons':read(p.parent/'qualification.json').get('reasons')} for p in tasks if (p.parent/'qualification.json').exists() and not read(p.parent/'qualification.json').get('qualified')]
new=sum(c['cost'] for c in calls)
value={'study':args.study,'completed':dict(done),'running':running,'failures':failed,'requests':len(calls),'new_conservative_cost':new,
       'project_conservative_cost':authorization['prior_stage_conservative_usd']+new,'approved_ceiling':authorization['project_limit_usd'],
       'unreconciled_requests':sum(c.get('cost_kind')!='provider_reported' and c['request_id'] not in authorization.get('transport_reconciliations',{}) for c in calls),
       'reconciled_transport_requests':len(authorization.get('transport_reconciliations',{})),
       'aggregate_account_bound_covered_requests':len(authorization.get('account_bound_reconciliation',{}).get('covered_request_ids',[]))}
print(json.dumps(value,indent=2))
