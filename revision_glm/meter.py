"""Concurrent, reservation-based OpenRouter meter for the frozen revision."""
from http.server import ThreadingHTTPServer,BaseHTTPRequestHandler
from pathlib import Path
import argparse,json,sqlite3,time,httpx,threading,uuid,os
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--limit',type=float,required=True);args=parser.parse_args()
key=os.getenv('OPENROUTER_API_KEY')
if not key:
 db=sqlite3.connect('file:'+str(Path.home()/'.cc-switch/cc-switch.db')+'?mode=ro',uri=True)
 provider_id=os.getenv('CC_SWITCH_PROVIDER_ID','fbd4c8ff-5c35-476d-9a5c-0b065f897e20')
 cfg=json.loads(db.execute('select settings_config from providers where id=?',(provider_id,)).fetchone()[0]);db.close();key=cfg['auth']['OPENAI_API_KEY']
headers={'Authorization':'Bearer '+key,'User-Agent':'ftec5660-reproduction/2.2'}
clients={'z-ai/glm-4.6':httpx.Client(timeout=240,trust_env=False),
         'openai/gpt-5':httpx.Client(timeout=240,trust_env=False,proxy=os.getenv('JUDGE_HTTPS_PROXY','http://127.0.0.1:7898') or None)}
folder=ROOT/'runs/glm/pinned';folder.mkdir(parents=True,exist_ok=True)
catalog=clients['z-ai/glm-4.6'].get('https://openrouter.ai/api/v1/models').json()['data']
models={m['id']:m for m in catalog if m['id'] in clients}
(folder/'formal_model_catalog.json').write_text(json.dumps(models,indent=2))
ledger=folder/'formal_usage.jsonl';lock=threading.Lock();reserved=0.0
spent=sum(json.loads(x)['cost'] for x in ledger.read_text().splitlines()) if ledger.exists() else 0.0
requests=folder/'requests';requests.mkdir(exist_ok=True)
def authorized_limit():
 override=folder/'budget_authorization.json'
 if override.exists():return float(json.loads(override.read_text())['meter_limit_usd'])
 return args.limit
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_GET(self):
  with lock: body=json.dumps({'spent':spent,'reserved':reserved,'limit':authorized_limit(),'models':list(models)}).encode()
  self.send_response(200);self.send_header('Content-Length',str(len(body)));self.end_headers();self.wfile.write(body)
 def do_POST(self):
  global spent,reserved
  data=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
  model=data.get('model')
  if model not in clients:self.send_error(400,'Model outside frozen scope');return
  data['provider']={'only':['z-ai' if model=='z-ai/glm-4.6' else 'openai'],'allow_fallbacks':False}
  cap=16384 if model=='z-ai/glm-4.6' else 4096
  data.pop('max_completion_tokens',None);data['max_tokens']=cap
  if data.get('stream'):data['stream_options']={'include_usage':True}
  pricing=models[model]['pricing'];pin=float(pricing['prompt']);pout=float(pricing['completion'])
  # UTF-8 byte count bounds ordinary text tokenization; extra allowance covers schemas.
  # Factor two covers route prices above the model catalogue's advertised minimum.
  reserve=2*((len(json.dumps(data).encode())+4096)*pin+cap*pout)
  with lock:
   if spent+reserved+reserve>authorized_limit():self.send_error(402,'Revision budget reached');return
   reserved+=reserve
  session=self.headers.get('x-opencode-session','unassigned');started=time.time();rid=uuid.uuid4().hex
  (requests/(rid+'.request.json')).write_text(json.dumps({'session':session,'body':data}),encoding='utf-8')
  record={'request_id':rid,'time':started,'session':session,'model':model,'parameters':{k:data[k] for k in ('temperature','top_p','max_tokens','reasoning','provider') if k in data}}
  response=None
  try:
   response=clients[model].post('https://openrouter.ai/api/v1/chat/completions',headers=headers,json=data)
   (requests/(rid+'.response.txt')).write_bytes(response.content)
   usage={};finish=[];provider=None;generation=None
   items=[]
   if data.get('stream'):
    items=[json.loads(line[6:]) for line in response.text.splitlines() if line.startswith('data: ') and line[6:]!='[DONE]']
   elif response.status_code==200:items=[response.json()]
   for item in items:
    usage=item.get('usage') or usage;provider=item.get('provider') or provider;generation=item.get('id') or generation
    finish.extend(x.get('finish_reason') for x in item.get('choices',[]) if x.get('finish_reason'))
   actual=usage.get('cost')
   cost=float(actual) if actual is not None else reserve
   record.update(status=response.status_code,usage=usage,cost=cost,cost_kind='provider_reported' if actual is not None else 'unreconciled_reserve',provider=provider,generation_id=generation,finish_reasons=finish)
  except Exception as exc:
   cost=reserve;record.update(error=type(exc).__name__,cost=cost,cost_kind='unreconciled_reserve')
  finally:
   with lock:
    reserved-=reserve;spent+=cost;record.update(total_cost=spent,seconds=time.time()-started)
    with ledger.open('a') as f:f.write(json.dumps(record)+'\n')
  if response is None:self.send_error(502,'Provider transport failure; reserve retained');return
  self.send_response(response.status_code);self.send_header('Content-Type',response.headers.get('content-type','application/json'));self.send_header('Content-Length',str(len(response.content)));self.end_headers()
  try:self.wfile.write(response.content)
  except (BrokenPipeError,ConnectionResetError):pass
print('Revision meter on 8879; remaining-run ceiling',args.limit,flush=True)
ThreadingHTTPServer(('127.0.0.1',8879),Handler).serve_forever()
