"""Compact status, budget and pending cells, independent of worker console output."""
import collections,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
folder=ROOT/'runs/full'
def read(p):return json.loads(p.read_text(encoding='utf-8'))
ledger=folder/'formal_usage.jsonl'
calls=[json.loads(x) for x in ledger.read_text(encoding='utf-8').splitlines()] if ledger.exists() else []
authorization=read(folder/'budget_authorization.json')
selected=list((folder/'formal').glob('*/q*/selection.json'))
tasks=list((folder/'formal').glob('*/q*/attempt*/task.json'))
done=collections.Counter(p.parts[-3] for p in selected if read(p).get('selected_attempt') is not None)
running=[{'cell':'/'.join(p.parts[-4:-1]),'seconds':round(time.time()-read(p)['started'])} for p in tasks if not (p.parent/'exit.json').exists()]
failed=[{'cell':'/'.join(p.parts[-4:-1]),'reasons':read(p.parent/'qualification.json').get('reasons')} for p in tasks if (p.parent/'qualification.json').exists() and not read(p.parent/'qualification.json').get('qualified')]
new=sum(c['cost'] for c in calls)
value={'completed':dict(done),'running':running,'failures':failed,'requests':len(calls),'new_conservative_cost':new,
       'project_conservative_cost':authorization['prior_stage_conservative_usd']+new,'approved_ceiling':authorization['project_limit_usd'],
       'unreconciled_requests':sum(c.get('cost_kind')!='provider_reported' for c in calls)}
print(json.dumps(value,indent=2))
