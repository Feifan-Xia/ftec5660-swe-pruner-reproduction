"""Capture the installed SDK's Azure wire schema using a local fake response."""
import json,os,sys,threading,time,zipfile
from pathlib import Path
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
ROOT=Path(__file__).resolve().parents[1]
for key in ['HTTP_PROXY','HTTPS_PROXY','ALL_PROXY','http_proxy','https_proxy','all_proxy']:os.environ.pop(key,None)
os.environ['NO_PROXY']=os.environ['no_proxy']='localhost,127.0.0.1,::1'
sys.path.insert(0,str(ROOT/'revision_subset/runtime'))
from tool_utils import PrunerBashTool
from openhands.sdk import LLM,Message,TextContent
z=zipfile.ZipFile(ROOT/'runs/author_evidence/swepruner-sweqa-reproduce.zip')
t=json.loads(z.read('traj-full-glm-pruner/streamlink/streamlink_q1.traj.json'))
s=next(e for e in t['events'] if e['type']=='SystemPromptEvent')
u=next(e for e in t['events'] if e['type']=='MessageEvent' and e.get('source')=='user')
captured=[]
class Handler(BaseHTTPRequestHandler):
    def log_message(self,*args):pass
    def do_POST(self):
        body=json.loads(self.rfile.read(int(self.headers['Content-Length'])));captured.append(body)
        base={'id':'offline-contract','model':'glm-4.6','created':int(time.time())}
        usage={'prompt_tokens':1,'completion_tokens':1,'total_tokens':2}
        if body.get('stream'):
            chunks=[dict(base,object='chat.completion.chunk',choices=[{'index':0,'delta':{'role':'assistant','content':'Offline contract capture complete.'},'finish_reason':None}]),dict(base,object='chat.completion.chunk',choices=[{'index':0,'delta':{},'finish_reason':'stop'}],usage=usage)]
            data=(''.join('data: '+json.dumps(c)+'\n\n' for c in chunks)+'data: [DONE]\n\n').encode();content_type='text/event-stream'
        else:
            data=json.dumps(dict(base,object='chat.completion',choices=[{'index':0,'message':{'role':'assistant','content':'Offline contract capture complete.'},'finish_reason':'stop'}],usage=usage)).encode();content_type='application/json'
        self.send_response(200);self.send_header('Content-Type',content_type);self.send_header('Content-Length',str(len(data)));self.end_headers();self.wfile.write(data)
server=ThreadingHTTPServer(('127.0.0.1',8897),Handler)
thread=threading.Thread(target=server.serve_forever,daemon=True);thread.start()
try:
    llm=LLM(model='azure/glm-4.6',api_key='offline-test',base_url='http://127.0.0.1:8897',api_version='2024-02-01',usage_id='agent')
    user=u['content'] if isinstance(u['content'],str) else '\n'.join(c['text'] for c in u['content'] if c.get('type')=='text')
    llm.completion(messages=[Message(role='system',content=[TextContent(text=s['system_prompt']['text'])]),Message(role='user',content=[TextContent(text=user)])],tools=PrunerBashTool.create(None),add_security_risk_prediction=True)
finally:server.shutdown()
assert len(captured)==1,len(captured)
body=captured[0];tool=next(t for t in body['tools'] if t['function']['name']=='pruner_bash')
out={'local_fake_endpoint':True,'actual_paid_requests':0,'wire_parameters':{k:v for k,v in body.items() if k not in ['messages','tools']},'tool':tool,'exact_author_tool_match':tool==s['tools'][0]}
(ROOT/'results/full/azure_wire_contract.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps({'exact_author_tool_match':out['exact_author_tool_match'],'wire_parameters':out['wire_parameters'],'required_fields':tool['function']['parameters']['required']},indent=2))
