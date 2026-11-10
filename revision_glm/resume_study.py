"""Resume the frozen schedule, adding bounded handling of non-JSON transport errors."""
import json,sys,time,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from revision_glm import run_study as study
import httpx
original_judge=study.judge
def resilient_judge(out):
 for retry in range(3):
  try:return original_judge(out)
  except (httpx.TransportError,json.JSONDecodeError) as exc:
   with (out/'judge_transport_recovery.jsonl').open('a',encoding='utf-8') as f:
    f.write(json.dumps({'time':time.time(),'recovery_attempt':retry,'error':type(exc).__name__,'policy':'Retry transport/invalid-JSON failure only; agent answer remains unchanged.'})+'\n')
   if retry==2:raise
study.judge=resilient_judge
if __name__=='__main__':study.main()
