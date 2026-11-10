"""Run a disjoint development question using the corrected GLM pipeline."""
import os,json,subprocess,sys,time,argparse
import httpx
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--mode',choices=['baseline','pruner','recovery'],default='baseline');parser.add_argument('--index',type=int,choices=[43,26,17],default=43);parser.add_argument('--repeat',type=int,default=0);args=parser.parse_args()
out=ROOT/f'runs/glm/pilot/{args.mode}/q{args.index}_r{args.repeat}'
if args.mode != 'baseline':
 health=httpx.get('http://127.0.0.1:8000/health',trust_env=False,timeout=15)
 health.raise_for_status()
 assert health.json()['model_loaded'] and health.json()['device'].startswith('cuda'), 'GPU pruner must be healthy before starting'
assert not (out/'task.json').exists(),'Preserve existing attempt'
out.mkdir(parents=True,exist_ok=True);(out/'questions').mkdir(exist_ok=True)
rows=[json.loads(x) for x in (ROOT/'upstream/downstream_eval/multi_turn/sweqa/questions/streamlink.jsonl').read_text().splitlines()]
(out/'questions/streamlink.jsonl').write_text(json.dumps({'question':rows[args.index]['question']})+'\n')
env=os.environ.copy();env.update(API_TYPE='openai',EXPERIMENT_TYPE='baseline',OPENAI_API_KEY='local-metered-route',OPENAI_BASE_URL='http://127.0.0.1:8878/v1',OPENHANDS_MODEL_NAME='openai/z-ai/glm-4.6',NO_PROXY='localhost,127.0.0.1,::1',no_proxy='localhost,127.0.0.1,::1',OPENHANDS_REPOS='streamlink',BASE_REPO_PATH=str(ROOT/'data'),QUESTIONS_PATH=str(out/'questions'),ANSWER_OUTPUT_PATH=str(out/'answers'),TRAJ_OUTPUT_PATH=str(out/'trajectories'),PROMPT_OUTPUT_PATH=str(out/'prompts'),MAX_ITERATION_PER_RUN='50',MAX_TIME_PER_QUESTION='1800',PRUNER_URL='http://127.0.0.1:8000/prune',PRUNE_THRESHOLD='0.4',OBSERVATION_LOG=str(out/'observations.json'),REPRO_SESSION_ID='glm-pilot-baseline-43-0',PYTHONPATH=os.pathsep.join([str(ROOT/'revision_glm/runtime'),str(ROOT)]))
env.update(EXPERIMENT_TYPE=args.mode,MAX_ITERATION_PER_RUN='250',PRUNE_THRESHOLD='0.5',REPRO_SESSION_ID=f'glm-pilot-{args.mode}-{args.index}-{args.repeat}')
env['FTEC_REPO_ROOT']='/home/feifa/ftec5660-swe-pruner/glm-repository/streamlink'
(out/'task.json').write_text(json.dumps({'phase':'glm_pilot',**vars(args),'started':time.time(),'max_iterations':250,'max_seconds':1800,'prune_threshold':0.5,'max_output_tokens':16384},indent=2))
with (out/'console.log').open('w') as log:
 p=subprocess.Popen([sys.executable,str(ROOT/'revision_glm/runtime/main.py')],cwd=ROOT/'data/streamlink',env=env,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
 try:code=p.wait(timeout=1920)
 except subprocess.TimeoutExpired:
  import signal
  os.killpg(p.pid,signal.SIGTERM);code=-15
(out/'exit.json').write_text(json.dumps({'returncode':code,'ended':time.time()}))
print('GLM pilot finished:',code,flush=True)
