"""Match fixed development/pilot questions to the authors' released evidence."""
import collections,json,statistics,urllib.parse,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
z=zipfile.ZipFile(ROOT/'runs/author_evidence/swepruner-sweqa-reproduce.zip')
questions=[json.loads(x)['question'] for x in (ROOT/'upstream/downstream_eval/multi_turn/sweqa/questions/streamlink.jsonl').read_text(encoding='utf-8').splitlines()]
result={}
for mode in ['glm','glm-pruner']:
    answers={r['question']:r for r in [json.loads(x) for x in z.read(f'answer-{mode}/streamlink_answers.jsonl').decode().splitlines()]}
    traj={t['question']:t for n in z.namelist() if n.startswith(f'traj-full-{mode}/streamlink/') and n.endswith('.traj.json') for t in [json.loads(z.read(n))]}
    cfg=json.loads(z.read(f'traj-full-{mode}/configs/streamlink_experiment_config.json'))
    print(mode,'endpoint host:',urllib.parse.urlparse(cfg['llm_config'].get('base_url','')).hostname)
    values=[]
    for i in [43,26,17,41,14,30,8,11,46,33,29]:
        a=answers[questions[i]];t=traj[questions[i]]
        commands=[e.get('action',{}) for e in t['events'] if e.get('type')=='ActionEvent' and e.get('action',{}).get('command')]
        values.append({'index':i,'tokens':a['prompt_tokens']+a['completion_tokens'],'reported_cost_field':a['token_cost'],
                       'commands':len(commands),'hints':sum(bool(c.get('context_focus_question')) for c in commands),
                       'first_commands':commands[:2]})
    result[mode]=values
    for label,indices in [('development',[43,26,17]),('old_subset',[41,14,30,8,11,46,33,29])]:
        print(mode,label,round(statistics.mean(r['tokens'] for r in values if r['index'] in indices),2))
(ROOT/'results/full/author_subset.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print('Development command samples:',json.dumps([r for r in result['glm-pruner'] if r['index'] in [43,26,17]],indent=2))
