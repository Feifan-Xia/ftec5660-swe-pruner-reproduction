"""Create a local review bundle with evidence, hashes, and credential checks."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import zipfile

ROOT = Path(__file__).resolve().parent

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--draft', action='store_true')
    args = parser.parse_args()
    if not args.draft:
        if subprocess.check_output(['git', 'diff', '--name-only', 'HEAD'], cwd=ROOT, text=True).strip():
            raise RuntimeError('Commit reviewed tracked-file changes before creating the final bundle')
        subprocess.run([sys.executable, str(ROOT/'audit_results.py')], cwd=ROOT, check=True)
        summary = json.loads((ROOT / 'results/formal_analysis.json').read_text())
        if summary['pending'] or summary['scheduled'] != 72 or not summary.get('final'):
            raise RuntimeError('Final bundle requires the approved complete 72-task inventory')
        if not (ROOT / 'report/SWE-Pruner_report.pdf').exists():
            raise RuntimeError('Final report is missing')
    tag = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    destination = ROOT / 'release' / (('draft-' if args.draft else 'submission-') + tag)
    destination.mkdir(parents=True, exist_ok=False)
    env = dict(line.split('=', 1) for line in (ROOT / '.env').read_text().splitlines() if '=' in line)
    secrets = [v.encode() for k, v in env.items() if any(word in k for word in ('KEY', 'TOKEN', 'SECRET')) and len(v) >= 16]
    history = subprocess.check_output(['git', 'log', '--all', '-p', '--format='], cwd=ROOT)
    if any(secret in history for secret in secrets):
        raise RuntimeError('Configured credential detected in Git history; review required')
    tracked = subprocess.check_output(['git', 'ls-files'], cwd=ROOT, text=True).splitlines()
    excluded = {'PROJECT_STATUS.md', 'DEBUG_DIARY.md'}
    paths = [ROOT / p for p in tracked if p not in excluded and not p.startswith('results/')]
    paths += [ROOT/'results'/name for name in ('formal_tasks.json', 'formal_tasks.csv', 'formal_analysis.json',
                                              'formal_comparison.png', 'formal_comparison.pdf')
              if (ROOT/'results'/name).exists()]
    paths += [ROOT/'results'/name for name in ('conclusion.txt', 'evidence_audit.json', 'pilot_tasks.json', 'pilot_tasks.csv', 'case_notes.md', 'judge_repairs.json', 'usage_recalibration.json')
              if (ROOT/'results'/name).exists()]
    paths += [ROOT / 'report' / ('SWE-Pruner_report_draft.pdf' if args.draft else 'SWE-Pruner_report.pdf')]
    evidence_names = ['api_usage.jsonl', 'network_checks.jsonl', 'pruner_numerical_validation.json',
                      'pruner_real_code_smoke.json', 'demo.json', 'pruner_service.jsonl']
    paths += [ROOT / 'runs' / name for name in evidence_names if (ROOT / 'runs' / name).exists()]
    phases = ['pilot'] if args.draft else ['pilot', 'formal']
    for phase in phases:
        paths += [p for p in (ROOT / 'runs' / phase).rglob('*') if p.is_file() and p.suffix in ('.json', '.jsonl', '.log', '.py')]
    aliases = [str(ROOT), ROOT.as_posix(), '/mnt/c/Users/feifa/Documents/ChatGPT/Reproduce Agent']
    manifest = []
    for source in sorted(set(paths)):
        if not source.exists():
            continue
        relative = source.relative_to(ROOT)
        data = source.read_bytes()
        original_hash = hashlib.sha256(data).hexdigest()
        if any(secret in data for secret in secrets):
            raise RuntimeError(f'Credential detected in {relative}; bundle is incomplete and must be reviewed')
        if relative.parts[0] != 'runs' and source.suffix in ('.json', '.jsonl', '.log', '.md', '.csv'):
            text = data.decode('utf-8')
            for alias in aliases:
                text = text.replace(alias, '$PROJECT_ROOT').replace(json.dumps(alias)[1:-1], '$PROJECT_ROOT')
            data = text.encode('utf-8')
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        manifest.append({'path': relative.as_posix(), 'bytes': len(data),
                         'sha256': hashlib.sha256(data).hexdigest(), 'source_sha256': original_hash})
    licenses = [('upstream/LICENSE', 'SWE-Pruner-LICENSE'), ('data/streamlink/LICENSE', 'Streamlink-LICENSE')]
    for source_name, name in licenses:
        source = ROOT / source_name
        if source.exists():
            folder = destination / 'third_party'
            folder.mkdir(exist_ok=True)
            data = source.read_bytes()
            (folder / name).write_bytes(data)
            manifest.append({'path': 'third_party/' + name, 'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()})
    if not args.draft:
        bundle = destination/'repository-history.bundle'
        subprocess.run(['git', 'bundle', 'create', str(bundle), '--all'], cwd=ROOT, check=True)
        subprocess.run(['git', 'bundle', 'verify', str(bundle)], cwd=ROOT, check=True, capture_output=True)
        data = bundle.read_bytes()
        manifest.append({'path':bundle.name, 'bytes':len(data), 'sha256':hashlib.sha256(data).hexdigest()})
    (destination / 'MANIFEST.json').write_text(json.dumps({'draft': args.draft,
        'git_revision': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip(),
        'transformation': 'Raw runs/ evidence is byte-preserved, including recorded local paths, content IDs and read lengths. Known project-root paths are replaced by $PROJECT_ROOT in other text files; source_sha256 records original file hashes.',
        'files': manifest}, indent=2), encoding='utf-8')
    archive = destination.with_suffix('.zip')
    with zipfile.ZipFile(archive, 'w', zipfile.ZIP_DEFLATED) as zipped:
        for path in destination.rglob('*'):
            if path.is_file():
                zipped.write(path, path.relative_to(destination))
    print(f'{len(manifest)} checked files: {archive}')

if __name__ == '__main__':
    main()
