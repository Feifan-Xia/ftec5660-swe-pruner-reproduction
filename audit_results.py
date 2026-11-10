"""Audit scheduled evidence and immutable runtime files before final reporting."""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DIMENSIONS = ['correctness', 'completeness', 'relevance', 'clarity', 'reasoning']

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--allow-pending', action='store_true')
    args = parser.parse_args()
    errors, pending = [], []
    approval = json.loads((ROOT/'configs/formal_approval.json').read_text())
    jobs = json.loads((ROOT/'runs/formal/schedule.json').read_text())
    expected = {(i,m,r) for i in approval['question_indices'] for m in approval['conditions'] for r in range(approval['repeats'])}
    actual = {(j['index'],j['mode'],j['repeat']) for j in jobs}
    if len(jobs) != 72 or len(actual) != len(jobs) or actual != expected:
        errors.append('Formal schedule does not match the approved 72 distinct attempts')
    frozen = json.loads((ROOT/'runs/formal/runtime_manifest.json').read_text())
    for name, expected_hash in frozen['files'].items():
        data = (ROOT/name).read_bytes()
        raw_match = hashlib.sha256(data).hexdigest() == expected_hash
        lf_match = hashlib.sha256(data.replace(b'\r\n', b'\n')).hexdigest() == frozen.get('canonical_lf_files', {}).get(name)
        if not raw_match and not lf_match:
            errors.append('Runtime changed: ' + name)
    question_rows = [json.loads(x) for x in (ROOT/'upstream/downstream_eval/multi_turn/sweqa/questions/streamlink.jsonl').read_text(encoding='utf-8').splitlines()]
    ledger = [json.loads(x) for x in (ROOT/'runs/api_usage.jsonl').read_text().splitlines()]
    spent = .0000297 + sum(x.get('charged_bound_usd', 0) for x in ledger if x.get('error') != 'ConnectError')
    checks = ROOT/'runs/network_checks.jsonl'
    if checks.exists():
        spent += sum(json.loads(x).get('usage', {}).get('opencode', {}).get('list_cost', 0) for x in checks.read_text().splitlines())
    if spent > approval['project_total_limit_usd'] + 1e-8:
        errors.append('Project budget ceiling exceeded')
    for job in jobs:
        label = f"{job['mode']}/q{job['index']}_r{job['repeat']}"
        path = ROOT/'runs/formal'/label
        if not (path/'exit.json').exists():
            pending.append(label)
            continue
        meta = json.loads((path/'task.json').read_text())
        if any(meta.get(k) != v for k,v in job.items()):
            errors.append('Task metadata mismatch: ' + label)
        exposed = [json.loads(x) for x in (path/'questions/streamlink.jsonl').read_text(encoding='utf-8').splitlines()]
        if exposed != [{'question': question_rows[job['index']]['question']}]:
            errors.append('Agent input differs from question-only source: ' + label)
        answers = [json.loads(x) for file in (path/'answers').rglob('*answers.jsonl') for x in file.read_text(encoding='utf-8').splitlines() if x.strip()]
        text = answers[-1].get('answer', '') if answers else ''
        completed = bool(text) and not text.startswith(('Error:', 'Timeout:', 'Unable to', 'No conversation'))
        if completed:
            if not (path/'score.json').exists():
                pending.append('judge/' + label)
            else:
                score = json.loads((path/'score.json').read_text())
                dimensions = [score['scores'][k] for k in DIMENSIONS]
                if any(type(x) is not int or not 1 <= x <= 10 for x in dimensions) or abs(score['mean']-sum(dimensions)/5)>1e-8:
                    errors.append('Rubric score mismatch: ' + label)
            if not list((path/'trajectories').rglob('*.traj.json')):
                errors.append('Completed answer lacks trajectory: ' + label)
        session = f"ftec5660-formal-{job['mode']}-{job['index']}-{job['repeat']}"
        usage = [row for row in ledger if row['session'] == session and row.get('usage')]
        if completed and not usage:
            errors.append('Completed answer lacks provider usage: ' + label)
    report = {'scheduled':len(jobs), 'pending':pending, 'errors':errors,
              'project_conservative_usd':spent, 'approved_limit_usd':approval['project_total_limit_usd'],
              'scope':'Schedule, runtime hashes, question-only input, answer-score linkage, trajectory/usage presence, budget.'}
    (ROOT/'results').mkdir(exist_ok=True)
    (ROOT/'results/evidence_audit.json').write_text(json.dumps(report, indent=2))
    print(f'Scheduled={len(jobs)} pending={len(pending)} errors={len(errors)} conservative_usd={spent:.6f}')
    if errors:
        raise RuntimeError('; '.join(errors))
    if pending and not args.allow_pending:
        raise RuntimeError('Formal evidence is still incomplete')

if __name__ == '__main__':
    main()
