"""Verify the independent GPT-5 judge with the authors' exact rubric."""
import json,sqlite3,sys,time
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from score_results import official_prompt,DIMENSIONS
out=ROOT/'runs/glm/pilot/baseline/q43_r0'
assert not (out/'judge_raw.json').exists(), 'Preserve previous judge attempt'
db=sqlite3.connect('file:C:/Users/feifa/.cc-switch/cc-switch.db?mode=ro',uri=True)
cfg=json.loads(db.execute('select settings_config from providers where id=?',('fbd4c8ff-5c35-476d-9a5c-0b065f897e20',)).fetchone()[0]);db.close()
client=httpx.Client(timeout=180,trust_env=False,proxy='http://127.0.0.1:7898',headers={'Authorization':'Bearer '+cfg['auth']['OPENAI_API_KEY']})
catalog=client.get('https://openrouter.ai/api/v1/models').json()['data']
model=next(x for x in catalog if x['id']=='openai/gpt-5')
(ROOT/'runs/glm/judge_catalog_entry.json').write_text(json.dumps(model,indent=2))
rows=[json.loads(x) for x in (ROOT/'upstream/downstream_eval/multi_turn/sweqa/questions/streamlink.jsonl').read_text().splitlines()]
candidate=[json.loads(x) for f in (out/'answers').rglob('*answers.jsonl') for x in f.read_text().splitlines() if x.strip()][-1]
row=rows[43]
prompt=official_prompt(row['question'],row.get('ground_truth') or row['answer'],candidate['answer'])
body={'model':'openai/gpt-5','max_tokens':4096,'reasoning':{'effort':'low'},'messages':[{'role':'user','content':prompt}]}
upper=(len(json.dumps(body).encode())+4096)*float(model['pricing']['prompt'])+4096*float(model['pricing']['completion'])
assert upper<.15, f'Pilot judge bound exceeds 0.15: {upper}'
started=time.time();response=client.post('https://openrouter.ai/api/v1/chat/completions',json=body)
if response.status_code != 200:
 (out/'judge_error.json').write_text(json.dumps({'status':response.status_code,'body':response.json()},indent=2))
 print(response.text)
response.raise_for_status();payload=response.json()
(out/'judge_raw.json').write_text(json.dumps(payload,indent=2))
with (ROOT/'runs/glm/judge_usage.jsonl').open('a') as f:f.write(json.dumps({'session':'judge-pilot-baseline-43-0','seconds':time.time()-started,'usage':payload.get('usage'),'provider':payload.get('provider'),'model':payload.get('model'),'parameters':{k:v for k,v in body.items() if k!='messages'}})+'\n')
scores=json.loads(payload['choices'][0]['message']['content'].strip().removeprefix('```json').removesuffix('```'))
assert all(type(scores.get(k)) is int and 1<=scores[k]<=10 for k in DIMENSIONS)
result={'scores':scores,'mean':sum(scores[k] for k in DIMENSIONS)/5,'judge_model':payload['model'],'same_model_judge':False,'author_filtered_eligible':all(scores[k]!=1 for k in DIMENSIONS)}
(out/'score.json').write_text(json.dumps(result,indent=2));print(json.dumps({'result':result,'usage':payload['usage']}))
