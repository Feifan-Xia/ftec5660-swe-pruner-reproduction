"""Stop only this revision's mixed-route experiment processes, preserving artifacts."""
import os,signal,subprocess,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
processes=[]
for line in subprocess.check_output(['ps','-eo','pid,args'],text=True).splitlines()[1:]:
 pid,args=line.strip().split(None,1)
 if ('python revision_glm/run_study.py' in args or 'python /mnt/c/Users/feifa/Documents/ChatGPT/Reproduce Agent/revision_glm/runtime/main.py' in args) and int(pid)!=os.getpid():processes.append((int(pid),args))
(ROOT/'runs/glm/formal/STOP_REASON.json').write_text(json.dumps({'time':time.time(),'reason':'Provider metadata revealed mixed Venice FP4 / Z.AI FP4 / Novita BF16 routing. Preserve this development batch; use a new fixed-provider formal study. Increase local prune-service wait for large files and concurrent requests.','pids':[p for p,_ in processes]},indent=2))
for pid,args in processes:
 try:
  if '/runtime/main.py' in args:os.killpg(pid,signal.SIGTERM)
  else:os.kill(pid,signal.SIGTERM)
 except ProcessLookupError:pass
print('Stopped project processes:',[p for p,_ in processes])
