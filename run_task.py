"""Run one fixed SWE-QA question through the authors' OpenHands pipeline."""
import argparse
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parent


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--mode', choices=['baseline', 'pruner', 'recovery'], required=True)
    parser.add_argument('--index', type=int, required=True)
    parser.add_argument('--repeat', type=int, default=0)
    parser.add_argument('--phase', choices=['pilot', 'formal'], default='pilot')
    args = parser.parse_args()
    selection = json.loads((ROOT / 'configs/task_selection.json').read_text())
    allowed = selection['pilot_indices' if args.phase == 'pilot' else 'evaluation_candidate_indices']
    if args.index not in allowed:
        parser.error('Question index is outside the declared phase split')
    if args.phase == 'formal' and not (ROOT / 'configs/formal_approval.json').exists():
        parser.error('Formal budget approval must be recorded first')
    source = ROOT / 'upstream/downstream_eval/multi_turn/sweqa'
    rows = [json.loads(x) for x in (source / 'questions/streamlink.jsonl').read_text().splitlines()]
    out = ROOT / f'runs/{args.phase}/{args.mode}/q{args.index}_r{args.repeat}'
    out.mkdir(parents=True, exist_ok=True)
    questions = out / 'questions'
    questions.mkdir(exist_ok=True)
    (questions / 'streamlink.jsonl').write_text(json.dumps({'question': rows[args.index]['question']}) + '\n')
    env = os.environ.copy()
    for line in (ROOT / '.env').read_text().splitlines():
        if '=' in line:
            k, v = line.split('=', 1)
            env[k] = v
    env.update(API_TYPE='openai', EXPERIMENT_TYPE=args.mode,
               OPENAI_BASE_URL='http://127.0.0.1:8765/v1',
               NO_PROXY='localhost,127.0.0.1,::1', no_proxy='localhost,127.0.0.1,::1',
               OPENHANDS_REPOS='streamlink', BASE_REPO_PATH=str(ROOT / 'data'),
               QUESTIONS_PATH=str(questions), ANSWER_OUTPUT_PATH=str(out / 'answers'),
               TRAJ_OUTPUT_PATH=str(out / 'trajectories'), PROMPT_OUTPUT_PATH=str(out / 'prompts'),
               MAX_ITERATION_PER_RUN='30', MAX_TIME_PER_QUESTION='600',
               PRUNER_URL='http://127.0.0.1:8000/prune', PRUNE_THRESHOLD='0.4',
               OBSERVATION_LOG=str(out / 'observations.json'),
               REPRO_SESSION_ID=f'ftec5660-{args.phase}-{args.mode}-{args.index}-{args.repeat}',
               PYTHONPATH=os.pathsep.join([str(ROOT), str(source / 'openhands-qa')]))
    (out / 'task.json').write_text(json.dumps(vars(args), indent=2))
    with (out / 'console.log').open('w') as log:
        process = subprocess.Popen([sys.executable, str(source / 'openhands-qa/main.py')],
                                   env=env, cwd=ROOT / 'data/streamlink', stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        try:
            code = process.wait(timeout=660)
        except subprocess.TimeoutExpired:
            import signal
            os.killpg(process.pid, signal.SIGTERM)
            code = -15
    (out / 'exit.json').write_text(json.dumps({'returncode': code}))
    print(out, code)


if __name__ == '__main__':
    main()
