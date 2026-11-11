"""Match author-run records to local question identities, retaining provenance."""
import json,statistics,zipfile,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text(encoding='utf-8'))
questions=[json.loads(x)['question'] for x in (ROOT/'upstream/downstream_eval/multi_turn/sweqa/questions/streamlink.jsonl').read_text(encoding='utf-8').splitlines()]
indices=read(ROOT/'revision_precision/protocol.json')['question_indices']
archive=ROOT/'runs/author_evidence/swepruner-sweqa-reproduce.zip';z=zipfile.ZipFile(archive)
local=read(ROOT/'results/precision/cells.json');records=[]
for mode,folder in [('baseline','answer-glm'),('pruner','answer-glm-pruner')]:
    answers=f'{folder}/streamlink_answers.jsonl';scores=f'{folder}/streamlink_answers_{mode}_score.jsonl'
    aa=[json.loads(x) for x in z.read(answers).decode().splitlines() if x.strip()]
    ss=[json.loads(x) for x in z.read(scores).decode().splitlines() if x.strip()]
    for index in indices:
        a=[r for r in aa if r['question']==questions[index]];s=[r for r in ss if r['question']==questions[index]]
        assert len(a)==len(s)==1
        own=[r for r in local if r['mode']==mode and r['index']==index];assert len(own)==3
        records.append({'index':index,'question_sha256':hashlib.sha256(questions[index].encode()).hexdigest(),'mode':mode,
            'author_answer_member':answers,'author_score_member':scores,
            'author_timestamp':a[0].get('timestamp'),'author_tokens':a[0]['prompt_tokens']+a[0]['completion_tokens'],
            'author_score':statistics.mean(s[0]['score'].values()),'local_paths':[r['path'] for r in own],
            'local_mean_tokens':statistics.mean(r['total_tokens'] for r in own),'local_mean_score':statistics.mean(r['score'] for r in own)})
means={mode:{key:statistics.mean(r[key] for r in records if r['mode']==mode) for key in ['author_tokens','author_score','local_mean_tokens','local_mean_score']} for mode in ['baseline','pruner']}
effects={key:100*(means['pruner'][key]/means['baseline'][key]-1) for key in means['baseline']}
author_saving=means['baseline']['author_tokens']-means['pruner']['author_tokens']
local_saving=means['baseline']['local_mean_tokens']-means['pruner']['local_mean_tokens']
gap=author_saving-local_saving
decomposition={'author_absolute_saving_per_task':author_saving,'local_absolute_saving_per_task':local_saving,'saving_gap_tokens':gap,
    'lower_local_full_tokens':means['baseline']['author_tokens']-means['baseline']['local_mean_tokens'],
    'higher_local_pruner_tokens':means['pruner']['local_mean_tokens']-means['pruner']['author_tokens']}
assert abs(decomposition['lower_local_full_tokens']+decomposition['higher_local_pruner_tokens']-gap)<1e-8
decomposition['lower_full_share_of_absolute_gap_percent']=100*decomposition['lower_local_full_tokens']/gap
decomposition['scope']='Arithmetic decomposition of the absolute saving gap. It does not identify a causal effect of provider, prompt or sampling.'
out={'source_definition':'Author fields are recalculated from the authors released executions, dated December 2025. Local fields summarize our three independent executions per identical question. Author data are reference evidence, not locally reproduced runs.',
     'archive_sha256':hashlib.sha256(archive.read_bytes()).hexdigest(),'question_indices':indices,'author_repetitions':1,'local_repetitions':3,'means':means,'relative_changes_percent':effects,'saving_gap_decomposition':decomposition,'records':records}
(ROOT/'results/full/author_same_questions.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps({'means':means,'relative_changes_percent':effects},indent=2))
