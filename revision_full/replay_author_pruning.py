"""Replay the first substantial original observation for each fixed pilot question."""
import argparse,hashlib,json,time,zipfile
from pathlib import Path
import httpx
ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser();parser.add_argument('--variant',choices=['bf16','fp32','fp32_original_fusion'],default='bf16');args=parser.parse_args()
z=zipfile.ZipFile(ROOT/'runs/author_evidence/swepruner-sweqa-reproduce.zip')
qs=[json.loads(x)['question'] for x in (ROOT/'upstream/downstream_eval/multi_turn/sweqa/questions/streamlink.jsonl').read_text(encoding='utf-8').splitlines()]
indices=[41,14,30,8,11,46,33,29]
by_question={t['question']:(n,t) for n in z.namelist() if n.startswith('traj-full-glm-pruner/streamlink/') and n.endswith('.traj.json') for t in [json.loads(z.read(n))]}
folder=ROOT/('runs/full/diagnostics/author_replay' if args.variant=='bf16' else 'runs/full/diagnostics/author_replay_'+args.variant);folder.mkdir(parents=True,exist_ok=True)
client=httpx.Client(trust_env=False,timeout=600)
for _ in range(120):
    try:
        response=client.get('http://127.0.0.1:8000/health',timeout=5);response.raise_for_status()
        expected='torch.float32' if args.variant.startswith('fp32') else 'torch.bfloat16'
        assert response.json()['dtype']==expected,response.json()
        if args.variant=='fp32_original_fusion':assert response.json()['attention_backend']=='original-mha-tiled-256'
        break
    except httpx.HTTPError:time.sleep(3)
else:raise RuntimeError('Pruner service unavailable')
rows=[]
for index in indices:
    name,t=by_question[qs[index]]
    choices=[(i,e['observation']) for i,e in enumerate(t['events']) if e.get('observation',{}).get('pruned') and len(e['observation'].get('original_output',''))>=1000]
    if not choices:
        rows.append({'index':index,'status':'no_substantial_observation'});continue
    ordinal,obs=choices[0];info=obs['prune_info'];target=folder/f'q{index}.json'
    if target.exists():rows.append(json.loads(target.read_text(encoding='utf-8')));continue
    started=time.time()
    response=client.post('http://127.0.0.1:8000/prune',json={'query':info['context_focus_question'],'code':obs['original_output'],'threshold':.5})
    response.raise_for_status();result=response.json()
    row={'index':index,'archive_path':name,'event':ordinal,'seconds':time.time()-started,'source_chars':len(obs['original_output']),
         'query':info['context_focus_question'],'author_raw_tokens':info['origin_token_cnt'],'author_left_tokens':info['left_token_cnt'],
         'local_raw_tokens':result['origin_token_cnt'],'local_left_tokens':result['left_token_cnt'],'local_error':result.get('error_msg'),
         'exact_pruned_text_match':result['pruned_code']==obs['output'],'author_score':info['score'],'local_score':result['score']}
    target.write_text(json.dumps(row,indent=2),encoding='utf-8');rows.append(row)
    print(json.dumps(row),flush=True)
destination='author_pruning_replay.json' if args.variant=='bf16' else 'author_pruning_replay_'+args.variant+'.json'
(ROOT/'results/full'/destination).write_text(json.dumps(rows,indent=2),encoding='utf-8')
