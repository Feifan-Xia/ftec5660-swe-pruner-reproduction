"""Carry historical spending into the unchanged approved project ceiling."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
old=json.loads((ROOT/'results/glm/audit.json').read_text(encoding='utf-8'))['checks']['project_conservative_usd']
folder=ROOT/'runs/full';folder.mkdir(exist_ok=True)
path=folder/'budget_authorization.json'
assert not path.exists(),'Preserve budget authorization history'
value={'project_limit_usd':12,'prior_stage_conservative_usd':old,'margin_usd':.15,
       'meter_limit_usd':12-old-.15,'authorization':'Existing explicit user approval of USD 12; a USD 28 increase is pending and is not assumed.'}
path.write_text(json.dumps(value,indent=2),encoding='utf-8')
print(json.dumps(value))
