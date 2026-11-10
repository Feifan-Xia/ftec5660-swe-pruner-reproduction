"""Capture a fresh reproduction's runtime before executing its formal schedule."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
FILES = ['run_formal.py', 'run_task.py', 'score_results.py', 'budget_proxy.py', 'serve_pruner.py',
         'recovery_tool.py', 'observation_store.py', 'configs/task_selection.json', 'configs/formal_approval.json',
         'upstream/downstream_eval/multi_turn/sweqa/openhands-qa/main.py',
         'upstream/downstream_eval/multi_turn/sweqa/openhands-qa/tool_utils.py',
         'upstream/swe-pruner/src/swe_pruner/model_structure.py',
         'upstream/swe-pruner/src/swe_pruner/prune_wrapper.py']

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, default=ROOT/'runs/formal/runtime_manifest.json')
    args = parser.parse_args()
    if args.output.exists():
        raise RuntimeError('Runtime snapshot already exists; preserve it and use a fresh checkout for a new experiment')
    files, canonical = {}, {}
    for name in FILES:
        data = (ROOT/name).read_bytes()
        files[name] = hashlib.sha256(data).hexdigest()
        canonical[name] = hashlib.sha256(data.replace(b'\r\n', b'\n')).hexdigest()
    result = {'git_revision_at_launch':subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT, text=True).strip(),
              'captured_pre_run':True, 'files':files, 'canonical_lf_files':canonical,
              'note':'Raw hashes preserve exact bytes; canonical hashes allow CRLF/LF checkout differences only.'}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2), encoding='utf-8')
    print(f'Captured {len(files)} runtime files: {args.output}')

if __name__=='__main__':
    main()
