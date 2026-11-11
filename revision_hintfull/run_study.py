"""Run balanced, complete paired GLM experiments with preserved retry evidence."""
import argparse,concurrent.futures,hashlib,json,os,signal,subprocess,sys,time
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from score_results import official_prompt,DIMENSIONS
MODES=['pruner']
OUT=ROOT/'runs/hintfull/formal'
WORKSPACE=Path.home()/'ftec5660-swe-pruner/paper-workspace'
REPO=WORKSPACE/'swe-repos/streamlink'
ROWS=[json.loads(x) for x in (ROOT/'upstream/downstream_eval/multi_turn/sweqa/questions/streamlink.jsonl').read_text(encoding='utf-8').splitlines()]
def read(path):return json.loads(path.read_text(encoding='utf-8'))
def write(path,data):path.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
def candidates(out):return [json.loads(x) for f in (out/'answers').rglob('*answers.jsonl') for x in f.read_text(encoding='utf-8').splitlines() if x.strip()]
def health(require_pruner=True):
 if require_pruner:
  r=httpx.get('http://127.0.0.1:8000/health',trust_env=False,timeout=15);r.raise_for_status()
  assert r.json()['model_loaded'] and r.json()['device'].startswith('cuda')
  assert r.json()['dtype']=='torch.float32', 'Require published default precision'
  assert r.json()['attention_backend']=='sdpa-query-tiled-256'
 r=httpx.get('http://127.0.0.1:8879/health',trust_env=False,timeout=15);r.raise_for_status()
 return r.json()
def run(job,attempt):
 mode,index,repeat=job['mode'],job['index'],job['repeat']
 out=OUT/mode/f'q{index}_r{repeat}'/f'attempt{attempt}'
 if (out/'exit.json').exists():return out
 if (out/'task.json').exists():raise RuntimeError(f'Unresolved process: {out}')
 if mode!='baseline':
  deadline=time.time()+1800
  while True:
   try:health();break
   except httpx.TransportError:
    if time.time()>deadline:raise
    time.sleep(5)
 health(require_pruner=False);out.mkdir(parents=True,exist_ok=True);(out/'questions').mkdir()
 (out/'questions/streamlink.jsonl').write_text(json.dumps({'question':ROWS[index]['question']})+'\n',encoding='utf-8')
 env=os.environ.copy()
 env.update(API_TYPE='openai',EXPERIMENT_TYPE=mode,OPENAI_API_KEY='local-metered-route',OPENAI_BASE_URL='http://127.0.0.1:8879/v1',OPENHANDS_MODEL_NAME='openai/z-ai/glm-4.6',NO_PROXY='localhost,127.0.0.1,::1',no_proxy='localhost,127.0.0.1,::1',OPENHANDS_REPOS='streamlink',BASE_REPO_PATH=str(REPO.parent),FTEC_REPO_ROOT=str(WORKSPACE),QUESTIONS_PATH=str(out/'questions'),ANSWER_OUTPUT_PATH=str(out/'answers'),TRAJ_OUTPUT_PATH=str(out/'trajectories'),PROMPT_OUTPUT_PATH=str(out/'prompts'),MAX_ITERATION_PER_RUN='50',MAX_TIME_PER_QUESTION='1800',PRUNER_URL='http://127.0.0.1:8000/prune',PRUNE_THRESHOLD='0.5',OBSERVATION_LOG=str(out/'observations.json'),REPRO_SESSION_ID=f'glm-hintfull-{mode}-{index}-{repeat}-a{attempt}',PYTHONPATH=os.pathsep.join([str(ROOT/'revision_hintfull/runtime'),str(ROOT)]),PYTHONUNBUFFERED='1')
 write(out/'task.json',dict(job,phase='schema_matched_full_control',attempt=attempt,started=time.time(),threshold=.5,max_iterations=50,max_seconds=1800,max_output_tokens=16384))
 with (out/'console.log').open('w',encoding='utf-8') as log:
  p=subprocess.Popen([sys.executable,str(ROOT/'revision_hintfull/runtime/main.py')],cwd=REPO,env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
  try:code=p.wait(timeout=1920)
  except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGTERM);code=-15
 write(out/'exit.json',{'returncode':code,'ended':time.time()})
 print(f'Agent finished {mode} q{index} r{repeat} a{attempt}',flush=True)
 return out
def qualify(out):
 logs=(out/'console.log').read_text(encoding='utf-8',errors='replace')
 answers=candidates(out);reasons=[]
 if read(out/'exit.json')['returncode']!=0:reasons.append('process_failure')
 if not answers or not answers[-1].get('answer','').strip() or answers[-1].get('answer')=='No answer found':reasons.append('missing_answer')
 if any(s in logs for s in ['Pruner request error','Pruner request failed','Pruner request returned None']):reasons.append('pruning_service_failure')
 if 'Revision budget reached' in logs:raise RuntimeError('Budget reached; preserve pending schedule')
 write(out/'qualification.json',{'qualified':not reasons,'reasons':reasons})
 return not reasons
def judge(out):
 if (out/'score.json').exists():return
 a=candidates(out)
 if not a or not a[-1].get('answer','').strip() or a[-1]['answer']=='No answer found':return
 task=read(out/'task.json');row=ROWS[task['index']]
 prompt=official_prompt(row['question'],row.get('ground_truth') or row['answer'],a[-1]['answer'])
 for n in range(3):
  raw=out/f'judge_raw_{n}.json'
  if raw.exists():payload=read(raw)
  else:
   try:r=httpx.post('http://127.0.0.1:8879/v1/chat/completions',trust_env=False,timeout=260,headers={'x-opencode-session':f"judge-hintfull-{task['mode']}-{task['index']}-{task['repeat']}-a{task['attempt']}-j{n}"},json={'model':'openai/gpt-5','max_tokens':4096,'reasoning':{'effort':'low'},'messages':[{'role':'user','content':prompt}]})
   except httpx.TransportError as exc:
    write(out/f'judge_transport_{n}.json',{'error':type(exc).__name__,'time':time.time()});continue
   if r.status_code==402:raise RuntimeError('Budget reached before judging')
   try:payload=r.json()
   except ValueError:
    write(out/f'judge_transport_{n}.json',{'status':r.status_code,'body':r.text,'time':time.time()});continue
   write(raw,payload)
  try:
   scores=json.loads(payload['choices'][0]['message']['content'].strip().removeprefix('```json').removesuffix('```'))
   assert all(type(scores.get(k)) is int and 1<=scores[k]<=10 for k in DIMENSIONS)
  except (KeyError,TypeError,ValueError,AssertionError):continue
  write(out/'score.json',{'scores':scores,'mean':sum(scores[k] for k in DIMENSIONS)/5,'judge_model':payload['model'],'judge_attempt':n,'author_filtered_eligible':all(scores[k]!=1 for k in DIMENSIONS)})
  return
 raise RuntimeError(f'Judge requires diagnosis: {out}')
def block(number,index,repeats=3):
 for repeat in range(repeats):
  shift=(number+repeat)%len(MODES)
  for mode in MODES[shift:]+MODES[:shift]:
   job={'mode':mode,'index':index,'repeat':repeat};selected=None
   for attempt in range(2):
    out=run(job,attempt);qualified=qualify(out);judge(out)
    if qualified:selected=attempt;break
   write(OUT/mode/f'q{index}_r{repeat}'/'selection.json',{'selected_attempt':selected,'policy':'First execution without infrastructure/answer-export failure; one bounded recovery attempt. Scores never trigger retries.'})
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--workers',type=int,default=8);parser.add_argument('--limit-questions',type=int);parser.add_argument('--repeats',type=int,choices=[1,3],default=3);args=parser.parse_args()
 protocol=read(ROOT/'revision_hintfull/protocol.json');indices=protocol['question_indices']
 if args.limit_questions:indices=indices[:args.limit_questions]
 frozen=read(OUT/'runtime_manifest.json')
 for name,expected in frozen['files'].items():
  assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected,f'Frozen source changed: {name}'
 health(require_pruner=False)
 with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as pool:
  jobs=[pool.submit(block,n,index,args.repeats) for n,index in enumerate(indices)]
  for future in concurrent.futures.as_completed(jobs):future.result()
 print(f'Processed {len(indices)*args.repeats*len(MODES)} scheduled cells in this invocation; fixed subset target is 48 and audit determines completion.',flush=True)
if __name__=='__main__':main()
