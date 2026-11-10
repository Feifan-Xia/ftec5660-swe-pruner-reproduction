"""Capture exact launch sources and a reviewable copy before starting a study."""
import hashlib,json,shutil,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
FILES=['revision_glm/run_study.py','revision_glm/meter.py','revision_glm/protocol.json','revision_glm/runtime/main.py','revision_glm/runtime/tool_utils.py','revision_glm/serve.py','revision_glm/memory_attention.py','serve_pruner.py','observation_store.py','recovery_tool.py','score_results.py','upstream/downstream_eval/multi_turn/sweqa/llm-as-judge.py','upstream/downstream_eval/multi_turn/sweqa/stats.py','upstream/swe-pruner/src/swe_pruner/model_structure.py','upstream/swe-pruner/src/swe_pruner/prune_wrapper.py']
dest=ROOT/'runs/glm/pinned/formal';dest.mkdir(parents=True,exist_ok=True)
assert not (dest/'runtime_manifest.json').exists(),'Preserve the launch snapshot'
manifest={'git_revision':subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),'captured_pre_run':True,'files':{},'canonical_lf_files':{}}
for name in FILES:
 data=(ROOT/name).read_bytes();manifest['files'][name]=hashlib.sha256(data).hexdigest();manifest['canonical_lf_files'][name]=hashlib.sha256(data.replace(b'\r\n',b'\n')).hexdigest()
 copy=dest/'frozen_source'/name;copy.parent.mkdir(parents=True,exist_ok=True);copy.write_bytes(data)
(dest/'runtime_manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('Captured',len(FILES),'launch sources.')
