"""Validate the actual source-root shell and schema against the author artifact."""
import ast,hashlib,json,os,subprocess,sys,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
os.environ['FTEC_REPO_ROOT']=str(Path.home()/'ftec5660-swe-pruner/paper-workspace')
source=(ROOT/'revision_subset/runtime/tool_utils.py').read_text(encoding='utf-8')
node=next(n for n in ast.parse(source).body if isinstance(n,ast.FunctionDef) and n.name=='_execute_bash_command')
ns={'os':os,'subprocess':subprocess};exec(compile(ast.Module(body=[node],type_ignores=[]),'shell','exec'),ns)
out=ns['_execute_bash_command']('pwd && test -f swe-repos/streamlink/src/streamlink/__init__.py && test -d swe-repos/conan && test -d swe-repos/reflex && test ! -e /mnt/c && test ! -d questions && echo SNAPSHOT_READY')
assert out=='/workspace\nSNAPSHOT_READY',out
manifest=json.loads((ROOT/'runs/author_evidence/workspace_manifest.json').read_text())
counts={r['repo']:sum(p.is_file() for p in (Path(os.environ['FTEC_REPO_ROOT'])/'swe-repos'/r['repo']).rglob('*')) for r in manifest}
assert all(counts[r['repo']]==r['files'] for r in manifest)
result={'shell':out,'file_counts':counts,'source_layout':'./swe-repos/{conan,reflex,streamlink}','status':'PASS'}
(ROOT/'results/full/subset_preflight.json').write_text(json.dumps(result,indent=2),encoding='utf-8')
print(json.dumps(result))
