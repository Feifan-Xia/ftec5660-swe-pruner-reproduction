"""Resume frozen studies after a documented transport/budget interruption.

Agent inputs and numerical sources stay frozen. Failed first attempts remain;
the original one-extra-agent-attempt rule applies. Extra judge requests use the
same saved answer and rubric, only after infrastructure/format failures.
"""
import argparse,importlib.util,json,sys,time
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
parser=argparse.ArgumentParser();parser.add_argument('--study',choices=['precision','hint','hintfull','recovery','optional'],required=True);parser.add_argument('--workers',type=int,default=3);parser.add_argument('--repeats',type=int,choices=[1,3],default=3);parser.add_argument('--receipt-only',action='store_true');parser.add_argument('--judge-only',action='store_true');parser.add_argument('--cell',help='Exact qINDEX_rREPEAT cell for a targeted judge-only resume');parser.add_argument('--one',action='store_true');args=parser.parse_args()
if args.cell:
    import re
    assert args.judge_only and re.fullmatch(r'q\d+_r\d+',args.cell),'--cell requires judge-only and an exact cell name'
source=ROOT/f'revision_{args.study}/run_study.py';spec=importlib.util.spec_from_file_location('frozen_runner',source);run=importlib.util.module_from_spec(spec);spec.loader.exec_module(run)
amendment={'scope':'Transport/budget recovery only; frozen model, prompts, task set and generation unchanged.','agent_policy':'Keep budget-interrupted attempt as failed infrastructure attempt; allow the original one bounded retry.','judge_policy':'Up to three additional requests after the original three infrastructure/format failures, on exactly the same saved answer. Accept first valid score regardless of value.','network':'Original project Sakura route restored for judges after failed direct-route availability check; direct GLM route remains unchanged.'}
note=ROOT/f'runs/{args.study}/formal/transport_recovery_amendment.json'
if not note.exists():note.write_text(json.dumps(amendment,indent=2),encoding='utf-8')
original_qualify=run.qualify;original_judge=run.judge
original_run=run.run
receipt_note=ROOT/f'runs/{args.study}/formal/receipt_completeness_amendment.json'
if not receipt_note.exists():
    run.write(receipt_note,{'time':time.time(),'policy':'Require usage receipts for every transmitted agent request in a selected run. A ConnectError reconciled as pre-transmission is exempt. Missing post-send usage makes the attempt an infrastructure failure; preserve its answer and score and use the original one bounded retry. Apply to every condition, regardless of scores or token direction.','reason':'An offline completeness audit found missing usage in precision/pruner q14_r1, q14_r2, q41_r2. Network errors can otherwise understate cumulative tokens.'})
repair_note=ROOT/f'runs/{args.study}/formal/transport_recovery_v2.json'
if not repair_note.exists():
    run.write(repair_note,{'time':time.time(),'agent_policy':'Permit attempt2 only when attempts0 and1 both failed due to budget_guard_interruption. Preserve all attempts. No score-based retries.','judge_policy':'Up to eight total stored judge slots on the identical answer. Stop invocation immediately on transport or HTTP error. Resume only after infrastructure diagnosis.','launch_policy':'Require at least USD0.25 unreserved meter headroom before starting another agent. One worker during recovery.'})
third_note=ROOT/f'runs/{args.study}/formal/transport_recovery_v3.json'
if not third_note.exists():
    run.write(third_note,{'time':time.time(),'agent_policy':'Permit attempt3 only when all three previous attempts were interrupted by budget protection. This follows simultaneous network reset/DNS failures and aggregate service-side billing reconciliation. Preserve every prior attempt and all costs. No score-based retries.','transport':'ConnectError before sending may retry up to four connection attempts; post-send failures still propagate and retain uncertainty. Frozen model and evaluation inputs unchanged.'})
def preflight(minimum=.25):
    state=run.health(require_pruner=False)
    if state['limit']-state['spent']-state['reserved']<minimum:
        raise RuntimeError('Insufficient reserved headroom; preserve pending schedule')
def guarded_run(job,attempt):
    out=run.OUT/job['mode']/f"q{job['index']}_r{job['repeat']}"/f'attempt{attempt}'
    if not (out/'exit.json').exists():preflight()
    return original_run(job,attempt)
def qualify(out):
    log=(out/'console.log').read_text(encoding='utf-8',errors='replace')
    if 'Revision budget reached' in log:
        run.write(out/'qualification.json',{'qualified':False,'reasons':['budget_guard_interruption'],'preserve_first_attempt':True})
        return False
    task=run.read(out/'task.json');session=f"glm-{args.study}-{task['mode']}-{task['index']}-{task['repeat']}-a{task['attempt']}"
    ledger=[json.loads(x) for x in (ROOT/'runs/full/formal_usage.jsonl').read_text().splitlines()]
    calls=[r for r in ledger if r['session']==session]
    missing=[r['request_id'] for r in calls if not r.get('usage') and r.get('error')!='ConnectError']
    if missing or not calls:
        for source in [out/'qualification.json',out.parent/'selection.json']:
            backup=source.with_name(source.stem+'_before_receipt_audit.json')
            if source.exists() and not backup.exists():backup.write_bytes(source.read_bytes())
        run.write(out/'qualification.json',{'qualified':False,'reasons':['usage_receipt_missing'],'request_ids':missing,'preserve_answer_and_score':True})
        return False
    return original_qualify(out)
def judge(out):
    if (out/'score.json').exists():return
    if not qualify(out):return
    answer=run.candidates(out)[-1];task=run.read(out/'task.json');row=run.ROWS[task['index']]
    prompt=run.official_prompt(row['question'],row.get('ground_truth') or row['answer'],answer['answer'])
    for n in range(8):
        raw=out/f'judge_raw_{n}.json';err=out/f'judge_transport_{n}.json'
        if err.exists() and not raw.exists():continue
        if raw.exists():payload=run.read(raw)
        else:
            preflight(.15)
            try:
                r=httpx.post('http://127.0.0.1:8879/v1/chat/completions',trust_env=False,timeout=260,headers={'x-opencode-session':f"judge-{args.study}-{task['mode']}-{task['index']}-{task['repeat']}-a{task['attempt']}-repair{n}"},json={'model':'openai/gpt-5','max_tokens':4096,'reasoning':{'effort':'low'},'messages':[{'role':'user','content':prompt}]})
                if r.status_code!=200:
                    run.write(err,{'status':r.status_code,'body':r.text,'time':time.time()})
                    raise RuntimeError(f'Judge HTTP {r.status_code}; stop for infrastructure diagnosis')
                payload=r.json();run.write(raw,payload)
            except (httpx.TransportError,ValueError) as exc:
                run.write(err,{'error':type(exc).__name__,'time':time.time()});raise RuntimeError('Judge transport/response failure; stop for diagnosis') from exc
        try:
            scores=json.loads(payload['choices'][0]['message']['content'].strip().removeprefix('```json').removesuffix('```'))
            assert all(type(scores.get(k)) is int and 1<=scores[k]<=10 for k in run.DIMENSIONS)
        except (KeyError,TypeError,ValueError,AssertionError):continue
        run.write(out/'score.json',{'scores':scores,'mean':sum(scores[k] for k in run.DIMENSIONS)/5,'judge_model':payload['model'],'judge_attempt':n,'author_filtered_eligible':all(scores[k]!=1 for k in run.DIMENSIONS),'repair_basis':'Same answer, restored transport, first valid score'})
        print(f'Repaired judge {out.parent.name} {task["mode"]}: {n}',flush=True);return
    raise RuntimeError(f'Judge remains unavailable after bounded repair: {out}')
def block(number,index,repeats=3):
    for repeat in range(repeats):
        shift=(number+repeat)%len(run.MODES)
        for mode in run.MODES[shift:]+run.MODES[:shift]:
            job={'mode':mode,'index':index,'repeat':repeat};selected=None
            cell=run.OUT/mode/f'q{index}_r{repeat}'
            for attempt in range(4):
                if attempt>=2:
                    previous=[run.read(cell/f'attempt{a}'/'qualification.json') for a in range(attempt)]
                    if any(p.get('reasons')!=['budget_guard_interruption'] for p in previous):break
                out=guarded_run(job,attempt)
                if qualify(out):
                    judge(out);selected=attempt;break
            run.write(cell/'selection.json',{'selected_attempt':selected,'policy':'First qualified execution; bounded infrastructure recovery under transport_recovery_v2.json. Scores never trigger retries.'})
unlocked_judge=judge
def judge(out):
    if (out/'score.json').exists():return
    lock=out/'judge_active.lock'
    try:handle=lock.open('x',encoding='utf-8')
    except FileExistsError:raise RuntimeError(f'Judge already active for {out}; wait for its owner before resuming')
    try:
        with handle:handle.write(json.dumps({'started':time.time(),'scope':'Exclusive evaluation of this saved answer'}))
        return unlocked_judge(out)
    finally:lock.unlink(missing_ok=True)
run.qualify=qualify;run.judge=judge;run.block=block
if args.receipt_only:
    for selection in sorted(run.OUT.glob('*/q*/selection.json')):
        selected=run.read(selection).get('selected_attempt')
        if selected is None:continue
        out=selection.parent/f'attempt{selected}'
        if qualify(out):continue
        if run.read(out/'qualification.json')['reasons']!=['usage_receipt_missing']:continue
        assert selected==0,'Receipt recovery preserves the original single retry bound'
        task=run.read(out/'task.json');job={k:task[k] for k in ['mode','index','repeat']}
        repaired=guarded_run(job,1)
        if not qualify(repaired):raise RuntimeError('Receipt recovery remains incomplete')
        judge(repaired)
        run.write(selection,{'selected_attempt':1,'policy':'First run with complete transmitted-request usage receipts; prior answer and score retained under receipt_completeness_amendment.json.'})
elif args.judge_only:
    for p in sorted(run.OUT.glob('*/q*/attempt*/exit.json')):
        if args.cell and p.parent.parent.name!=args.cell:continue
        out=p.parent
        if (out/'score.json').exists() or not qualify(out):continue
        judge(out)
        if args.one:break
else:
    sys.argv=[str(source),'--workers',str(args.workers),'--repeats',str(args.repeats)]
    run.main()
