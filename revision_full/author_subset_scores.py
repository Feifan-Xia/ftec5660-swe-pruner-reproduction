"""Keep the published archive's subset scores and denominator explicit."""
import json,statistics,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
z=zipfile.ZipFile(ROOT/'runs/author_evidence/swepruner-sweqa-reproduce.zip')
qs=[json.loads(x)['question'] for x in (ROOT/'upstream/downstream_eval/multi_turn/sweqa/questions/streamlink.jsonl').read_text(encoding='utf-8').splitlines()]
indices=json.loads((ROOT/'revision_precision/protocol.json').read_text(encoding='utf-8'))['question_indices']
scores={}
for mode,suffix in [('baseline','glm'),('pruner','glm-pruner')]:
    scores[mode]={r['question']:r['score'] for r in [json.loads(x) for x in z.read(f'answer-{suffix}/streamlink_answers_{mode}_score.jsonl').decode().splitlines()]}
rows=[]
for i in indices:
    item={'index':i,'scores':{m:s.get(qs[i]) for m,s in scores.items()}}
    item['complete_pair']=all(item['scores'].values())
    item['author_filtered_eligible']=item['complete_pair'] and all(v!=1 for s in item['scores'].values() for v in s.values())
    rows.append(item)
out={'rows':rows,'all_available_means':{m:statistics.mean(statistics.mean(r['scores'][m].values()) for r in rows if r['scores'][m]) for m in scores},
     'filtered_pair_n':sum(r['author_filtered_eligible'] for r in rows),
     'filtered_pair_means':{m:statistics.mean(statistics.mean(r['scores'][m].values()) for r in rows if r['author_filtered_eligible']) for m in scores}}
(ROOT/'results/full/author_subset_scores.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in out.items() if k!='rows'},indent=2))
