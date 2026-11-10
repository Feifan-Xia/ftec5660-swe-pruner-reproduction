"""Fill missing judge scores after evaluation, preserving every earlier response."""
import argparse
import json
from pathlib import Path
import httpx
from score_results import official_prompt, DIMENSIONS

ROOT = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--phase', choices=['pilot','formal'], default='formal')
    args = parser.parse_args()
    references = [json.loads(x) for x in (ROOT/'upstream/downstream_eval/multi_turn/sweqa/questions/streamlink.jsonl').read_text(encoding='utf-8').splitlines()]
    repaired, unresolved = [], []
    for meta in sorted((ROOT/'runs'/args.phase).glob('*/*/task.json')):
        directory = meta.parent
        if (directory/'score.json').exists():
            if json.loads((directory/'score.json').read_text()).get('judge_retry'):
                repaired.append(str(directory.relative_to(ROOT)))
            continue
        if not (directory/'exit.json').exists():
            continue
        answers = [json.loads(x) for p in (directory/'answers').rglob('*answers.jsonl') for x in p.read_text(encoding='utf-8').splitlines() if x.strip()]
        candidate = answers[-1].get('answer','') if answers else ''
        if not candidate or candidate.startswith(('Error:','Timeout:','Unable to','No conversation')):
            continue
        task=json.loads(meta.read_text())
        reference=references[task['index']]
        prompt=official_prompt(reference['question'], reference.get('ground_truth') or reference['answer'], candidate)
        for attempt in range(1,3):
            raw_path=directory/f'judge_retry_{attempt}_raw.json'
            if raw_path.exists():
                continue
            session=f"judge-{args.phase}-{task['mode']}-{task['index']}-{task['repeat']}-retry{attempt}"
            try:
                response=httpx.post('http://127.0.0.1:8877/v1/chat/completions', trust_env=False,
                    headers={'x-opencode-session':session},
                    json={'model':'deepseek-v4.1-flash','temperature':0,'max_tokens':4096,
                          'response_format':{'type':'json_object'},'messages':[{'role':'user','content':prompt}]}, timeout=180)
                response.raise_for_status()
                payload=response.json()
                raw_path.write_text(json.dumps(payload,indent=2),encoding='utf-8')
                scores=json.loads(payload['choices'][0]['message']['content'])
                if any(type(scores.get(k)) is not int or not 1<=scores[k]<=10 for k in DIMENSIONS):
                    raise ValueError('Invalid score schema')
                result={'scores':scores,'mean':sum(scores[k] for k in DIMENSIONS)/5,
                        'judge_model':payload['model'],'same_model_judge':True,
                        'author_filtered_eligible':all(scores[k]!=1 for k in DIMENSIONS),
                        'judge_max_tokens':4096,'judge_retry':attempt,
                        'repair_reason':'Original response did not yield a valid complete rubric JSON; original artifacts retained.'}
                (directory/'score.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
                repaired.append(str(directory.relative_to(ROOT)))
                print('Scored:',directory,flush=True)
                break
            except Exception as exc:
                if not raw_path.exists():
                    raw_path.write_text(json.dumps({'error':type(exc).__name__,'detail':str(exc)[:300]}),encoding='utf-8')
                print('Judge attempt incomplete:',directory,type(exc).__name__,flush=True)
        if not (directory/'score.json').exists():
            unresolved.append(str(directory.relative_to(ROOT)))
    output={'repaired':repaired,'unresolved':unresolved,
            'policy':'Only missing scores; identical model/rubric/temperature; output ceiling 4096 instead of 2048; up to two preserved repair attempts.'}
    (ROOT/'results/judge_repairs.json').write_text(json.dumps(output,indent=2))
    print(json.dumps(output,indent=2))
    if unresolved:
        raise RuntimeError('Judge repairs remain unresolved')

if __name__=='__main__':
    main()
