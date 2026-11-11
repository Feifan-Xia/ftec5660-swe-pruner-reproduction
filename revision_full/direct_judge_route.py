"""Route the project's isolated judge proxy directly to OpenRouter."""
from pathlib import Path
import yaml
ROOT=Path(__file__).resolve().parents[1]
p=ROOT/'runs/network_glm/config.yaml'
backup=p.with_name('config.before-direct-judge.yaml')
assert not backup.exists(),'Route change already prepared'
backup.write_bytes(p.read_bytes())
data=yaml.safe_load(p.read_text(encoding='utf-8'))
assert data['mixed-port']==7898
data['rules']=['DOMAIN,openrouter.ai,DIRECT',*data['rules']]
p.write_text(yaml.safe_dump(data,allow_unicode=True,sort_keys=False),encoding='utf-8')
print('Prepared isolated port-7898 direct OpenRouter route; private configuration remains under runs/network_glm.')
