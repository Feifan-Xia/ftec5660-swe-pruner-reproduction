"""Predeclared goal-shift probe: can an agent recover a literal from a saved observation?"""
import argparse,ast,concurrent.futures,hashlib,json,random,sys,time
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from observation_store import ObservationStore
OUT=ROOT/'runs/glm/pinned/mechanism';OUT.mkdir(parents=True,exist_ok=True)
def write(p,x):p.write_text(json.dumps(x,indent=2,ensure_ascii=False),encoding='utf-8')
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def prepare():
 plan=OUT/'plan.json'
 if plan.exists():cases=read(plan)['cases']
 else:
  eligible=[]
  for p in sorted((ROOT/'data/streamlink/src/streamlink/plugins').glob('*.py')):
   source=p.read_text(encoding='utf-8');lines=source.splitlines()
   if not 25<=len(lines)<=180:continue
   tree=ast.parse(source);constants=[]
   for n in ast.walk(tree):
    if isinstance(n,ast.Assign) and isinstance(n.value,ast.Constant) and isinstance(n.value.value,str) and 8<=len(n.value.value)<=120 and '\n' not in n.value.value:
     for target in n.targets:
      if isinstance(target,ast.Name) and target.id.isupper():constants.append((n.lineno,target.id,n.value.value))
   if constants:
    line,name,value=sorted(constants)[0]
    eligible.append({'path':p.relative_to(ROOT/'data/streamlink').as_posix(),'line_count':len(lines),'target_line':line,'constant':name,'expected':value,'source_sha256':hashlib.sha256(source.encode()).hexdigest()})
  random.Random(5660).shuffle(eligible);cases=eligible[:8]
  write(plan,{'frozen_before_model_calls':True,'selection':'Sorted pinned plugin files with 25–180 lines; earliest uppercase literal string assignment of length 8–120; shuffle seed 5660; first eight of all eligible files. Keep cases even when pruning retains the answer.','eligible_files':len(eligible),'initial_goal':'Which imported modules and classes does this plugin depend on?','followup_goal':'Return the exact literal value of the selected constant.','conditions':['full','pruned','recoverable'],'repeats':3,'max_tool_turns':4,'scoring':'Exact equality after decoding a JSON string, UNKNOWN allowed; no LLM judge.','cases':cases})
 for i,case in enumerate(cases):
  path=OUT/f'case{i}.json'
  if path.exists():continue
  source=(ROOT/'data/streamlink'/case['path']).read_text(encoding='utf-8')
  r=httpx.post('http://127.0.0.1:8000/prune',json={'code':source,'query':'Which imported modules and classes does this plugin depend on?','threshold':.5},trust_env=False,timeout=180);r.raise_for_status();pruned=r.json()
  assert not pruned.get('error_msg'),pruned.get('error_msg')
  write(path,dict(case,source=source,prune=pruned,target_value_retained=case['expected'] in pruned['pruned_code']))
def run(i,mode,repeat):
 case=read(OUT/f'case{i}.json');out=OUT/mode/f'case{i}_r{repeat}.json';out.parent.mkdir(exist_ok=True)
 if out.exists():return
 store=ObservationStore();obs_id=store.put(case['source']);context=case['source'] if mode=='full' else case['prune']['pruned_code']
 question=f"What is the exact string literal assigned to {case['constant']} in {case['path']}? Return only a valid JSON string containing the value; return the JSON string \"UNKNOWN\" if the provided evidence cannot establish it. Use saved original lines when an expansion tool is available."
 if mode=='recoverable':context+=f'\n\nOriginal output saved as {obs_id}, {case["line_count"]} lines. Use expand with inclusive one-based start/end lines to recover details.'
 messages=[{'role':'system','content':'Answer using only the provided code evidence and tool outputs. The observation was previously filtered for a different investigation goal. Preserve exact spelling and punctuation.'},{'role':'user','content':question+'\n\nSaved observation:\n'+context}]
 tool={'type':'function','function':{'name':'expand','description':'Recover exact original lines from a saved tool output when details are needed.','parameters':{'type':'object','properties':{'observation_id':{'type':'string'},'start':{'type':'integer'},'end':{'type':'integer'}},'required':['observation_id','start','end']}}}
 responses=[];answer='';started=time.time()
 for turn in range(5):
  body={'model':'z-ai/glm-4.6','temperature':0,'max_tokens':2048,'messages':messages}
  if mode=='recoverable' and turn<4:body['tools']=[tool]
  r=httpx.post('http://127.0.0.1:8879/v1/chat/completions',json=body,headers={'x-opencode-session':f'mechanism-{mode}-{i}-{repeat}'},trust_env=False,timeout=260)
  r.raise_for_status();payload=r.json();responses.append(payload);msg=payload['choices'][0]['message'];messages.append(msg)
  if not msg.get('tool_calls'):answer=msg.get('content') or '';break
  for call in msg['tool_calls']:
   try:result=store.expand(**json.loads(call['function']['arguments']))
   except (ValueError,TypeError,KeyError) as exc:result=str(exc)
   messages.append({'role':'tool','tool_call_id':call['id'],'content':result})
 try:decoded=json.loads(answer.strip().removeprefix('```json').removesuffix('```'))
 except ValueError:decoded=None
 write(out,{'case':i,'mode':mode,'repeat':repeat,'answer':answer,'correct':decoded==case['expected'],'target_value_retained':case['target_value_retained'],'seconds':time.time()-started,'reads':store.reads,'responses':responses,'messages':messages})
 print(f'Mechanism {mode} case{i} r{repeat}: exact={decoded==case["expected"]}, expands={len(store.reads)}',flush=True)
def main():
 parser=argparse.ArgumentParser();parser.add_argument('--prepare-only',action='store_true');args=parser.parse_args();prepare()
 if args.prepare_only:return
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  futures=[pool.submit(run,i,mode,repeat) for repeat in range(3) for i in range(8) for mode in ['full','pruned','recoverable']]
  for f in concurrent.futures.as_completed(futures):f.result()
if __name__=='__main__':main()
