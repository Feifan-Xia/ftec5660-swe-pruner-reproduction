"""Read only the published Streamlink evidence; never expose credential fields."""
import collections,hashlib,json,statistics,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
archive=zipfile.ZipFile(ROOT/'runs/author_evidence/swepruner-sweqa-reproduce.zip')
def read(name):return json.loads(archive.read(name))
def rows(name):return [json.loads(x) for x in archive.read(name).decode().splitlines() if x.strip()]
local_questions=rows('answer-glm/streamlink_answers.jsonl')
report={}
paired_scores={}
answers_by_mode={}
for mode in ['glm','glm-pruner']:
    config=read(f'traj-full-{mode}/configs/streamlink_experiment_config.json')
    answers=rows(f'answer-{mode}/streamlink_answers.jsonl')
    name='pruner' if 'pruner' in mode else 'baseline'
    scores=rows(f'answer-{mode}/streamlink_answers_{name}_score.jsonl')
    paired_scores[mode]={s['question']:s for s in scores}
    answers_by_mode[mode]={s['question']:s for s in answers}
    trajectories=[read(n) for n in archive.namelist() if n.startswith(f'traj-full-{mode}/streamlink/') and n.endswith('.traj.json')]
    observations=[e.get('observation',{}) for t in trajectories for e in t['events'] if e.get('type')=='ObservationEvent']
    actions=[e.get('action',{}) for t in trajectories for e in t['events'] if e.get('type')=='ActionEvent']
    llm=config['llm_config']
    sanitized={'timestamp':config['timestamp'],'llm_config_keys':list(llm),
               'llm':{k:llm.get(k) for k in ['model','temperature','top_p','max_output_tokens','usage_id']},
               'processing':config['processing_config'],'prune':config.get('prune_config'),
               'tools':config.get('tools')}
    # Keep only safe scalar pruning settings; URLs may contain credentials.
    if sanitized['prune']:
        sanitized['prune']={k:v for k,v in sanitized['prune'].items() if k in ['threshold','prune_threshold','enabled']}
    score_values=[statistics.mean(s['score'].values()) for s in scores]
    stats={'config':sanitized,'answer_count':len(answers),'trajectory_count':len(trajectories),
           'mean_token_cost':statistics.mean(r['token_cost'] for r in answers),
           'mean_input_plus_output':statistics.mean(r['prompt_tokens']+r['completion_tokens'] for r in answers),
           'answer_accounting_mismatch_count':sum(r['token_cost']!=r['prompt_tokens']+r['completion_tokens'] for r in answers),
           'mean_rounds':statistics.mean(sum(e.get('source') in ['agent','user'] for e in t['events']) for t in trajectories),
           'scores_count':len(scores),'mean_score_all':statistics.mean(score_values),
           'pruning_tasks':sum(any(e.get('observation',{}).get('pruned') for e in t['events']) for t in trajectories),
           'prune_calls':sum(bool(o.get('pruned')) for o in observations),
           'hints':sum(bool(a.get('context_focus_question')) for a in actions),
           'action_count':len(actions),'action_kinds':dict(collections.Counter(a.get('kind') for a in actions))}
    report[mode]=stats
common=set.intersection(*(set(d) for d in paired_scores.values()))
eligible=[q for q in common if all(all(v!=1 for v in d[q]['score'].values()) for d in paired_scores.values())]
report['paired_filtered']={'common':len(common),'eligible':len(eligible),'conditions':{m:{
    'score':statistics.mean(statistics.mean(paired_scores[m][q]['score'].values()) for q in eligible),
    'token_cost':statistics.mean(answers_by_mode[m][q]['token_cost'] for q in eligible),
    'input_plus_output':statistics.mean(answers_by_mode[m][q]['prompt_tokens']+answers_by_mode[m][q]['completion_tokens'] for q in eligible)} for m in paired_scores}}
target=ROOT/'results/full/author_evidence_summary.json'
target.write_text(json.dumps(report,indent=2,ensure_ascii=False),encoding='utf-8')
print(json.dumps(report,indent=2,ensure_ascii=False))
