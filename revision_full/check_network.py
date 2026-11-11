"""Check public model metadata routes without credentials or paid requests."""
from concurrent.futures import ThreadPoolExecutor
import httpx,time,json
def probe(proxy):
    start=time.time()
    try:
        with httpx.Client(proxy=proxy,trust_env=False,timeout=20) as client:
            r=client.get('https://openrouter.ai/api/v1/models')
            return {'route':proxy or 'direct','status':r.status_code,'seconds':time.time()-start}
    except Exception as e:return {'route':proxy or 'direct','error':type(e).__name__,'seconds':time.time()-start}
with ThreadPoolExecutor(2) as pool:
    for result in pool.map(probe,[None,'http://127.0.0.1:7898']):print(json.dumps(result),flush=True)
