"""Byte-preserved, secret-scanned evidence snapshot for the completed subset."""
import hashlib,json,re,subprocess,sys,zipfile
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT))
from revision_glm.package import credential_literals

names=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard'],cwd=ROOT,text=True,encoding='utf-8').splitlines()
paths={ROOT/name for name in names if (ROOT/name).is_file()}
for folder in ['runs/precision','runs/optional','runs/hint','runs/hintfull','runs/recovery','runs/priming','runs/full']:
    for p in (ROOT/folder).rglob('*'):
        if not p.is_file() or '__pycache__' in p.parts:continue
        if p.suffix in {'.json','.jsonl','.txt','.py','.md'} or (p.name=='console.log' and 'formal' in p.parts):paths.add(p)
for name in ['runs/author_evidence/swepruner-sweqa-reproduce.zip','runs/author_evidence/provenance.json','runs/author_evidence/workspace_manifest.json','runs/api_usage.jsonl','runs/network_checks.jsonl','runs/glm/usage.jsonl','runs/glm/judge_usage.jsonl','runs/glm/formal_usage.jsonl','runs/glm/pinned/formal_usage.jsonl','upstream/LICENSE']:
    p=ROOT/name
    if p.exists():paths.add(p)
for p in (ROOT/'upstream/downstream_eval/multi_turn/sweqa').rglob('*'):
    if p.is_file() and '__pycache__' not in p.parts:paths.add(p)
for stage in ['precision','optional','hint','hintfull','recovery','priming']:
    snapshot=json.loads((ROOT/f'runs/{stage}/formal/runtime_manifest.json').read_text(encoding='utf-8'))
    for name in snapshot['files']:
        p=(ROOT/name).resolve();assert p.is_relative_to(ROOT) and p.is_file()
        paths.add(p)
secrets=credential_literals();manifest=[]
for p in sorted(paths):
    relative=p.relative_to(ROOT).as_posix()
    assert not any(part in {'.git','.env','models','.venv-pruner','network_glm'} for part in p.relative_to(ROOT).parts)
    data=p.read_bytes()
    assert not any(key in data for key in secrets),'Credential literal in '+relative
    assert not re.search(rb'(?<![A-Za-z0-9_-])sk-(?:or-v1-|proj-|ant-api\d+-)?[A-Za-z0-9_-]{32,}',data),'Possible credential in '+relative
    manifest.append({'path':relative,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
stamp=datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ');dest=ROOT/'release'/f'SWE-Pruner-subset-evidence-{stamp}.zip';dest.parent.mkdir(exist_ok=True)
meta={'scope':'Completed fixed-subset evidence snapshot. Full48-question extension remains pending authorization and execution; this archive is not a claim of full-goal completion.',
      'git_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
      'git_status':subprocess.check_output(['git','status','--short'],cwd=ROOT,text=True,encoding='utf-8'),
      'primary_cells':72,'required_hint_diagnostic_cells':24,'mechanism_cells':72,
      'author_observation_replays':131,'priming_development_cells':6,'priming_gate':'failed quality tolerance; all official scores retained',
      'secret_scan':'Known local API credential literals and key-shaped patterns checked before writing; proxy configurations, environment files, model weights and virtual environments excluded.',
      'files':manifest}
print(f'Scanned {len(manifest)} files; writing evidence snapshot.',flush=True)
with zipfile.ZipFile(dest,'x',zipfile.ZIP_DEFLATED,compresslevel=6) as z:
    for p in sorted(paths):z.write(p,p.relative_to(ROOT).as_posix())
    z.writestr('EVIDENCE_MANIFEST.json',json.dumps(meta,indent=2))
    z.writestr('GIT_HISTORY.txt',subprocess.check_output(['git','log','--oneline','--all'],cwd=ROOT,text=True))
with zipfile.ZipFile(dest) as z:
    assert z.testzip() is None
    for row in manifest:assert hashlib.sha256(z.read(row['path'])).hexdigest()==row['sha256']
print(json.dumps({'archive':str(dest),'bytes':dest.stat().st_size,'files':len(manifest),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest(),'zip_and_file_hashes_verified':True}))
