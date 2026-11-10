"""Execute the approved, counterbalanced formal schedule without replacing failures."""
import argparse
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent
MODES = ['baseline', 'pruner', 'recovery']

def schedule(indices, repeats=3):
    jobs = []
    for repeat in range(repeats):
        for number, index in enumerate(indices):
            shift = (number + repeat) % 3
            for mode in MODES[shift:] + MODES[:shift]:
                jobs.append({'phase': 'formal', 'mode': mode, 'index': index, 'repeat': repeat})
    return jobs

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--plan-only', action='store_true')
    args = parser.parse_args()
    selection = json.loads((ROOT / 'configs/task_selection.json').read_text())
    approval_path = ROOT / 'configs/formal_approval.json'
    approval = json.loads(approval_path.read_text()) if approval_path.exists() else {}
    indices = approval.get('question_indices', selection['evaluation_candidate_indices'][:8])
    if len(set(indices)) != len(indices) or not set(indices) <= set(selection['evaluation_candidate_indices']):
        raise ValueError('Invalid formal subset')
    jobs = schedule(indices)
    if args.plan_only:
        print(json.dumps(jobs, indent=2))
        return
    if approval.get('approved') is not True or approval.get('project_total_limit_usd', 0) <= 1:
        raise RuntimeError('Explicit formal budget approval is required')
    manifest = ROOT / 'runs/formal/schedule.json'
    manifest.parent.mkdir(parents=True, exist_ok=True)
    if manifest.exists() and json.loads(manifest.read_text()) != jobs:
        raise RuntimeError('Existing formal schedule differs; preserve the frozen experiment')
    manifest.write_text(json.dumps(jobs, indent=2))
    for job in jobs:
        directory = ROOT / f"runs/formal/{job['mode']}/q{job['index']}_r{job['repeat']}"
        if (directory / 'task.json').exists() and not (directory / 'exit.json').exists():
            raise RuntimeError(f'Unresolved existing attempt: {directory}; inspect its process before continuing')
        if not (directory / 'exit.json').exists():
            command = [sys.executable, str(ROOT / 'run_task.py')]
            for key, value in job.items():
                command += ['--' + key, str(value)]
            subprocess.run(command, check=True)
        if not (directory / 'score.json').exists():
            result = subprocess.run([sys.executable, str(ROOT / 'score_results.py'), str(directory)])
            if result.returncode:
                print(f'Judge pending for {directory}; task remains in the inventory.', flush=True)
        subprocess.run([sys.executable, str(ROOT / 'summarize_results.py'), '--phase', 'formal'],
                       check=True, stdout=subprocess.DEVNULL)
        # Stop promptly on budget exhaustion; never manufacture the remaining attempts.
        if 'Reproduction pilot budget reached' in (directory / 'console.log').read_text(errors='replace'):
            raise RuntimeError('Proxy budget exhausted; remaining schedule is pending')

if __name__ == '__main__':
    main()
