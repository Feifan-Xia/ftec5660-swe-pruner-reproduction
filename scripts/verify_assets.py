"""Offline verification of pinned question/model assets and repository revisions."""
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
def digest(path):
    value = hashlib.sha256()
    with path.open('rb') as handle:
        for chunk in iter(lambda: handle.read(8*1024*1024), b''):
            value.update(chunk)
    return value.hexdigest()

selection = json.loads((ROOT/'configs/task_selection.json').read_text())
for folder, expected in [('upstream', selection['upstream_commit']), ('data/streamlink', selection['repo_commit'])]:
    revision = subprocess.check_output(['git','rev-parse','HEAD'], cwd=ROOT/folder, text=True).strip()
    if not revision.startswith(expected):
        raise RuntimeError(f'Revision mismatch: {folder}')
questions = ROOT/'upstream/downstream_eval/multi_turn/sweqa/questions/streamlink.jsonl'
if digest(questions) != selection['source_sha256']:
    raise RuntimeError('Question file hash mismatch')
assets = json.loads((ROOT/'configs/model_assets.json').read_text())
for asset in assets:
    path = ROOT/asset['path']
    if path.stat().st_size != asset['bytes'] or digest(path) != asset['sha256']:
        raise RuntimeError(f"Model asset mismatch: {asset['path']}")
print(f'Verified repository revisions, question hash, and {len(assets)} model assets.')
