"""Aggregate per-request usage, task outcomes, and recovery/pruning evidence."""
import argparse
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def summarize(phase):
    ledger_path = ROOT / 'runs/api_usage.jsonl'
    calls = [json.loads(x) for x in ledger_path.read_text(encoding='utf-8').splitlines()] if ledger_path.exists() else []
    results = []
    for meta in sorted((ROOT / 'runs' / phase).glob('*/*/task.json')):
        task = json.loads(meta.read_text())
        directory = meta.parent
        session = f"ftec5660-{phase}-{task['mode']}-{task['index']}-{task['repeat']}"
        requests = [x for x in calls if x['session'] == session]
        usage = [x.get('usage', {}) for x in requests]
        answers = [json.loads(line) for p in (directory / 'answers').rglob('*answers.jsonl')
                   for line in p.read_text(encoding='utf-8').splitlines() if line.strip()]
        answer = answers[-1] if answers else {}
        score_path = directory / 'score.json'
        score = json.loads(score_path.read_text()) if score_path.exists() else {}
        text = answer.get('answer', '')
        valid = bool(text) and not text.startswith(('Error:', 'Timeout:', 'Unable to', 'No conversation'))
        exit_path = directory / 'exit.json'
        exit_code = json.loads(exit_path.read_text()).get('returncode') if exit_path.exists() else None
        status = 'running' if exit_code is None else ('answered' if valid else 'failed')
        observations = directory / 'observations.json'
        reads = json.loads(observations.read_text(encoding='utf-8')).get('reads', []) if observations.exists() else []
        row = dict(phase=phase, mode=task['mode'], question_index=task['index'], repeat=task['repeat'],
                   status=status, completed_answer=valid, score=score.get('mean'), seconds=answer.get('time_cost'),
                   api_calls=len(requests), input_tokens=sum(x.get('prompt_tokens', 0) for x in usage),
                   output_tokens=sum(x.get('completion_tokens', 0) for x in usage),
                   cash_cost=sum(x.get('cost', 0) for x in usage),
                   go_allowance=sum(x.get('opencode', {}).get('allowance', 0) for x in usage),
                   recovery_reads=len(reads), repeated_lines=sum(x['repeated_lines'] for x in reads),
                   author_filtered_eligible=score.get('author_filtered_eligible'), path=str(directory.relative_to(ROOT)))
        row['total_tokens'] = row['input_tokens'] + row['output_tokens']
        results.append(row)
    out = ROOT / 'results'
    out.mkdir(exist_ok=True)
    (out / f'{phase}_tasks.json').write_text(json.dumps(results, indent=2), encoding='utf-8')
    if results:
        with (out / f'{phase}_tasks.csv').open('w', newline='', encoding='utf-8') as file:
            writer = csv.DictWriter(file, fieldnames=list(results[0])); writer.writeheader(); writer.writerows(results)
    print(json.dumps(results, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--phase', choices=['pilot','formal'], default='pilot')
    summarize(parser.parse_args().phase)
