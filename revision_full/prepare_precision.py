"""Create an isolated precision correction; keep earlier subset evidence intact."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
dest=ROOT/'revision_precision';dest.mkdir(exist_ok=True)
assert not (ROOT/'runs/precision/formal/runtime_manifest.json').exists()
runner=(ROOT/'revision_subset/run_study.py').read_text(encoding='utf-8')
runner=runner.replace('runs/subset/formal','runs/precision/formal').replace('glm-subset-','glm-precision-').replace('judge-subset-','judge-precision-')
runner=runner.replace('revision_subset/protocol.json','revision_precision/protocol.json').replace("phase='artifact_aligned_subset'","phase='artifact_aligned_fp32'")
runner=runner.replace("assert r.json()['model_loaded'] and r.json()['device'].startswith('cuda')","assert r.json()['model_loaded'] and r.json()['device'].startswith('cuda')\n  assert r.json()['dtype']=='torch.float32', 'Require published default precision'")
(dest/'run_study.py').write_text(runner,encoding='utf-8')
protocol=json.loads((ROOT/'revision_subset/protocol.json').read_text(encoding='utf-8'))
protocol.update(version='artifact-aligned-fixed-subset-fp32-v2',pruner_weight_dtype='float32',
                precision_basis='Released online_serving.py omits dtype; direct loading in pinned Transformers produces FP32 parameters. Published checkpoint contains BF16 backbone tensors and 15 FP32 tensors; previous explicit BF16 cast rounded the latter.',
                previous_stage='Complete first repetition in runs/subset/formal uses BF16 weights and remains a separate diagnostic.')
(dest/'protocol.json').write_text(json.dumps(protocol,indent=2,ensure_ascii=False),encoding='utf-8')
freeze=(ROOT/'revision_subset/freeze.py').read_text(encoding='utf-8').replace('revision_subset/run_study.py','revision_precision/run_study.py').replace('revision_subset/protocol.json','revision_precision/protocol.json').replace('revision_full/serve.py','revision_full/serve_fp32.py').replace('runs/subset/formal','runs/precision/formal')
(dest/'freeze.py').write_text(freeze,encoding='utf-8')
analysis=(ROOT/'revision_subset/analyze.py').read_text(encoding='utf-8').replace('results/subset','results/precision').replace('revision_subset/protocol.json','revision_precision/protocol.json').replace('runs/subset/formal/','runs/precision/formal/').replace('glm-subset-','glm-precision-')
(dest/'analyze.py').write_text(analysis,encoding='utf-8')
effects=(ROOT/'revision_subset/effects.py').read_text(encoding='utf-8').replace('results/subset','results/precision').replace('revision_subset/protocol.json','revision_precision/protocol.json')
(dest/'effects.py').write_text(effects,encoding='utf-8')
print('Prepared precision-only correction of the matched subset, pending GPU replay validation.')
