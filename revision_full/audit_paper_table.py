"""Recompute Table 2 quantities directly from the authors' released archive."""
import json,statistics,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
z=zipfile.ZipFile(ROOT/'runs/author_evidence/swepruner-sweqa-reproduce.zip')
def rows(n):return [json.loads(x) for x in z.read(n).decode().splitlines() if x.strip()]
refs={'streamlink':{'glm':[318200,145100],'claude':[611200,557100]},'reflex':{'glm':[142300,101200],'claude':[1081600,866800]},'conan':{'glm':[175900,116600],'claude':[654700,520700]}}
table=[]
for repo in refs:
    for model in ['glm','claude']:
        score_dicts=[];record=[]
        for position,suffix in enumerate(['','-pruner']):
            mode=model+suffix;condition='pruner' if suffix else 'baseline'
            answers=rows(f'answer-{mode}/{repo}_answers.jsonl')
            scores=rows(f'answer-{mode}/{repo}_answers_{condition}_score.jsonl')
            score_dicts.append({s['question']:s for s in scores})
            trajectories=[json.loads(z.read(n)) for n in z.namelist() if n.startswith(f'traj-full-{mode}/{repo}/') and n.endswith('.traj.json')]
            item={'repo':repo,'model':model,'condition':condition,'n_answers':len(answers),'n_trajectories':len(trajectories),
                  'published_tokens':refs[repo][model][position],
                  'artifact_token_cost':statistics.mean(a['token_cost'] for a in answers),
                  'artifact_input_plus_output':statistics.mean(a['prompt_tokens']+a['completion_tokens'] for a in answers),
                  'artifact_rounds':statistics.mean(sum(e.get('source') in ['agent','user'] for e in t['events']) for t in trajectories)}
            record.append(item)
        common=set(score_dicts[0])&set(score_dicts[1])
        eligible=[q for q in common if all(all(v!=1 for v in s[q]['score'].values()) for s in score_dicts)]
        for position,item in enumerate(record):
            item['score_pairs']=len(eligible)
            item['artifact_filtered_score']=statistics.mean(statistics.mean(score_dicts[position][q]['score'].values()) for q in eligible)
            table.append(item)
out=ROOT/'results/full/author_table_audit.json';out.write_text(json.dumps(table,indent=2),encoding='utf-8')
for r in table:print(f"{r['repo']:10} {r['model']:6} {r['condition']:8} paper={r['published_tokens']/1000:7.1f}K artifact={r['artifact_input_plus_output']/1000:7.1f}K score={r['artifact_filtered_score']:.4f} rounds={r['artifact_rounds']:.4f}")
