"""Record resolved Azure defaults without sending any API request."""
import inspect,json
from pathlib import Path
from openhands.sdk import LLM
ROOT=Path(__file__).resolve().parents[1]
llm=LLM(model='azure/glm-4.6',api_key='offline-test',base_url='http://127.0.0.1:8897',api_version='2024-02-01',usage_id='agent')
row={k:getattr(llm,k) for k in ['model','temperature','top_p','max_output_tokens']}
row['temperature_field_default']=LLM.model_fields['temperature'].default
row['source_path']=inspect.getfile(LLM)
root=Path(inspect.getfile(LLM)).parent
matches=[]
for p in root.rglob('*.py'):
    for n,line in enumerate(p.read_text().splitlines(),1):
        if any(w in line for w in ['temperature','strict','required']):matches.append({'file':p.name,'line':n,'text':line.strip()})
row['source_matches']=matches
(ROOT/'results/full/sdk_azure_defaults.json').write_text(json.dumps(row,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in row.items() if k!='source_matches'},indent=2))
for r in matches:
    if 'temperature' in r['text']:print(r)
