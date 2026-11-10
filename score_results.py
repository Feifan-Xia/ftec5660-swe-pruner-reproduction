"""Score answers with the exact official SWE-QA rubric via the metered API."""
import argparse
import ast
import json
from pathlib import Path
import httpx

ROOT = Path(__file__).resolve().parent
DIMENSIONS = ['correctness', 'completeness', 'relevance', 'clarity', 'reasoning']


def official_prompt(question, reference, candidate):
    source = ROOT / 'upstream/downstream_eval/multi_turn/sweqa/llm-as-judge.py'
    tree = ast.parse(source.read_text(encoding='utf-8'))
    function = next(x for x in tree.body if isinstance(x, ast.FunctionDef) and x.name == 'score_answer')
    assignment = next(x for x in function.body if isinstance(x, ast.Assign)
                      and any(isinstance(t, ast.Name) and t.id == 'prompt' for t in x.targets))
    expression = ast.Expression(assignment.value)
    return eval(compile(expression, str(source), 'eval'), {'__builtins__': {}},
                dict(question=question, reference=reference, candidate=candidate))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('run_dir', type=Path)
    args = parser.parse_args()
    task = json.loads((args.run_dir / 'task.json').read_text())
    rows = [json.loads(x) for x in (ROOT / 'upstream/downstream_eval/multi_turn/sweqa/questions/streamlink.jsonl').read_text().splitlines()]
    reference = rows[task['index']]
    files = list((args.run_dir / 'answers').rglob('*answers.jsonl'))
    candidates = [json.loads(x) for f in files for x in f.read_text().splitlines() if x.strip()]
    if not candidates:
        raise RuntimeError('No candidate answer available; preserve task as execution failure')
    candidate = candidates[-1]
    prompt = official_prompt(reference['question'], reference.get('ground_truth') or reference['answer'], candidate['answer'])
    response = httpx.post('http://127.0.0.1:8877/v1/chat/completions', trust_env=False,
        headers={'x-opencode-session': f"judge-{task['phase']}-{task['mode']}-{task['index']}-{task['repeat']}"},
        json={'model':'deepseek-v4.1-flash', 'temperature':0, 'max_tokens':2048,
              'response_format':{'type':'json_object'}, 'messages':[{'role':'user','content':prompt}]}, timeout=180)
    response.raise_for_status()
    payload = response.json()
    (args.run_dir / 'judge_raw.json').write_text(json.dumps(payload, indent=2))
    scores = json.loads(payload['choices'][0]['message']['content'])
    if any(type(scores.get(k)) is not int or not 1 <= scores[k] <= 10 for k in DIMENSIONS):
        raise ValueError('Invalid rubric score schema')
    result = {'scores':scores, 'mean':sum(scores[k] for k in DIMENSIONS)/5,
              'judge_model':payload['model'], 'same_model_judge':True,
              'author_filtered_eligible':all(scores[k] != 1 for k in DIMENSIONS)}
    (args.run_dir / 'score.json').write_text(json.dumps(result, indent=2))
    print(result)


if __name__ == '__main__':
    main()
