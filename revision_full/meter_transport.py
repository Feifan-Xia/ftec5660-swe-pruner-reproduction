"""Transport observability wrapper; frozen meter and API bodies stay intact."""
import json,os,runpy,sys,time,threading
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parents[1]
if os.getenv('FTEC_UPSTREAM_STREAMING')=='1':
    sys.path.insert(0,str(ROOT))
    from revision_full.sse_transport import install
    install()
original=httpx.Client.post
pause_until=0.0
state_lock=threading.Lock()
def post(self,*args,**kwargs):
    global pause_until
    for attempt in range(4):
        with state_lock:delay=max(0,pause_until-time.time())
        if delay:time.sleep(min(delay,15))
        try:return original(self,*args,**kwargs)
        except httpx.TransportError as exc:
            # ConnectError occurs before request transmission. Only these errors
            # can retry inside one reservation; post-send errors propagate intact.
            row={'time':time.time(),'error':type(exc).__name__,'detail':str(exc),'cause':str(exc.__cause__),'connection_attempt':attempt}
            with state_lock:
                pause_until=time.time()+10
                with (ROOT/'runs/full/transport_errors.jsonl').open('a',encoding='utf-8') as f:f.write(json.dumps(row)+'\n')
            if not isinstance(exc,httpx.ConnectError) or attempt==3:raise
httpx.Client.post=post
os.environ.setdefault('AGENT_HTTPS_PROXY','')
os.environ.setdefault('JUDGE_HTTPS_PROXY','http://127.0.0.1:7898')
if os.getenv('FTEC_FRESH_CONNECTIONS')=='1':
    original_init=httpx.Client.__init__
    def fresh_init(self,*args,**kwargs):
        kwargs.setdefault('limits',httpx.Limits(max_keepalive_connections=0))
        original_init(self,*args,**kwargs)
    httpx.Client.__init__=fresh_init
sys.argv=[str(ROOT/'revision_full/meter.py'),'--limit','12']
runpy.run_path(str(ROOT/'revision_full/meter.py'),run_name='__main__')
