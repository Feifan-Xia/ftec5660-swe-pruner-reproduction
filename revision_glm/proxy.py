"""Meter a bounded OpenRouter pilot without exposing credentials to the runner."""
from http.server import HTTPServer,BaseHTTPRequestHandler
from pathlib import Path
import argparse,json,sqlite3,time,httpx
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--limit',type=float,default=.30);args=parser.parse_args()
db=sqlite3.connect('file:C:/Users/feifa/.cc-switch/cc-switch.db?mode=ro',uri=True)
cfg=json.loads(db.execute('select settings_config from providers where id=?',('fbd4c8ff-5c35-476d-9a5c-0b065f897e20',)).fetchone()[0]);db.close()
key=cfg['auth']['OPENAI_API_KEY']
client=httpx.Client(timeout=240,trust_env=False)
headers={'Authorization':'Bearer '+key,'User-Agent':'ftec5660-glm-reproduction/2.0'}
catalog=client.get('https://openrouter.ai/api/v1/models',headers=headers).json()['data']
model=next(x for x in catalog if x['id']=='z-ai/glm-4.6')
folder=ROOT/'runs/glm';folder.mkdir(parents=True,exist_ok=True)
(folder/'model_catalog_entry.json').write_text(json.dumps(model,indent=2))
price=model['pricing']; pin=float(price['prompt']);pout=float(price['completion'])
ledger=folder/'usage.jsonl'
spent=sum(json.loads(x)['cost'] for x in ledger.read_text().splitlines()) if ledger.exists() else 0
class Handler(BaseHTTPRequestHandler):
 def log_message(self,*args):pass
 def do_POST(self):
  global spent
  data=json.loads(self.rfile.read(int(self.headers['Content-Length'])))
  if data.get('model')!='z-ai/glm-4.6':self.send_error(400,'Model outside pilot scope');return
  data.pop('max_completion_tokens',None);data['max_tokens']=16384
  if data.get('stream'):data['stream_options']={'include_usage':True}
  reserve=(len(json.dumps(data).encode())+4096)*pin+16384*pout
  if spent+reserve>args.limit:self.send_error(402,'GLM pilot budget reached');return
  session=self.headers.get('x-opencode-session','unassigned');started=time.time()
  try:
   r=client.post('https://openrouter.ai/api/v1/chat/completions',headers=headers,json=data)
   usage={};finish=[]
   if data.get('stream'):
    for line in r.text.splitlines():
     if line.startswith('data: ') and line[6:]!='[DONE]':
      item=json.loads(line[6:]);usage=item.get('usage') or usage
      finish.extend(x.get('finish_reason') for x in item.get('choices',[]) if x.get('finish_reason'))
   elif r.status_code==200:
    item=r.json();usage=item.get('usage',{});finish=[x.get('finish_reason') for x in item.get('choices',[])]
   cost=usage.get('cost');cost=float(cost) if cost is not None else (usage.get('prompt_tokens',0)*pin+usage.get('completion_tokens',0)*pout if usage else reserve)
   spent+=cost
   record={'time':time.time(),'session':session,'status':r.status_code,'seconds':time.time()-started,'usage':usage,'cost':cost,'total_cost':spent,'finish_reasons':finish,'parameters':{k:data[k] for k in ('model','temperature','top_p','max_tokens') if k in data}}
   with ledger.open('a') as f:f.write(json.dumps(record)+'\n')
   self.send_response(r.status_code);self.send_header('Content-Type',r.headers.get('content-type','application/json'));self.send_header('Content-Length',str(len(r.content)));self.end_headers();self.wfile.write(r.content)
  except Exception as e:
   spent+=reserve
   with ledger.open('a') as f:f.write(json.dumps({'time':time.time(),'session':session,'error':type(e).__name__,'cost':reserve,'total_cost':spent})+'\n')
   self.send_error(502,'Provider transport error; conservative reserve retained')
print('GLM pilot proxy ready on 8878; limit',args.limit,flush=True)
HTTPServer(('127.0.0.1',8878),Handler).serve_forever()
