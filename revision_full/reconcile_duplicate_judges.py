"""Restore the predeclared first-valid-score policy after concurrent judging."""
import argparse,json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
def write(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    p.write_text(json.dumps(v,indent=2),encoding='utf-8')
parser=argparse.ArgumentParser();parser.add_argument('--study',required=True);args=parser.parse_args()
ledger=[json.loads(x) for x in (ROOT/'runs/full/formal_usage.jsonl').read_text(encoding='utf-8').splitlines()]
records=[]
for selection in (ROOT/f'runs/{args.study}/formal').glob('*/q*/selection.json'):
    attempt=read(selection).get('selected_attempt')
    if attempt is None:continue
    d=selection.parent/f'attempt{attempt}';task=read(d/'task.json')
    prefix=f"judge-{args.study}-{task['mode']}-{task['index']}-{task['repeat']}-a{attempt}-"
    receipts=[]
    for row in sorted((r for r in ledger if r['session'].startswith(prefix)),key=lambda r:r['time']):
        p=ROOT/'runs/full/requests'/f"{row['request_id']}.response.txt"
        if not p.exists():continue
        try:
            payload=read(p);scores=json.loads(payload['choices'][0]['message']['content'].strip().removeprefix('```json').removesuffix('```'))
            assert set(scores)=={'correctness','completeness','relevance','clarity','reasoning'}
            assert all(type(v) is int and 1<=v<=10 for v in scores.values())
        except (ValueError,KeyError,TypeError,AssertionError):continue
        receipts.append((row,payload,scores))
    if len(receipts)<=1:continue
    bodies=[read(ROOT/'runs/full/requests'/f"{r['request_id']}.request.json")['body'] for r,_,_ in receipts]
    assert all(body==bodies[0] for body in bodies),'Multiple valid scores have different evaluation inputs'
    first,payload,scores=receipts[0];scorepath=d/'score.json';old=read(scorepath)
    note=d/'duplicate_judge_reconciliation.json'
    if not note.exists():
        write(d/'score_before_duplicate_reconciliation.json',old)
        write(note,{'policy':'First valid score in request-start order, irrespective of score. Duplicate judge responses and their billing remain preserved.','reason':'Concurrent resume and active driver both requested the same saved answer.','all_valid_request_ids':[r['request_id'] for r,_,_ in receipts],'selected_request_id':first['request_id'],'previous_mean':old['mean'],'selected_mean':sum(scores.values())/5})
    if old['scores']!=scores:
        old.update(scores=scores,mean=sum(scores.values())/5,author_filtered_eligible=all(v!=1 for v in scores.values()),judge_receipt_id=first['request_id'],repair_basis='First valid receipt; duplicate judging reconciled by predeclared order')
        write(scorepath,old)
    records.append(read(note))
write(ROOT/f'results/{args.study}/duplicate_judge_audit.json',{'duplicates':records,'scope':'Completed selected executions only; retain every request, response and cost.'})
print(json.dumps({'duplicate_cells':len(records),'selected_means':[r['selected_mean'] for r in records]}))
