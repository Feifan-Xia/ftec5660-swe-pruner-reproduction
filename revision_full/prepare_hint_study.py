"""Freeze an explicit activation-policy ablation, separately from reproduction."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
dest=ROOT/'revision_hint';(dest/'runtime').mkdir(parents=True,exist_ok=True)
assert not (ROOT/'runs/hint/formal/runtime_manifest.json').exists()
for name in ['main.py','tool_utils.py']:
    text=(ROOT/'revision_subset/runtime'/name).read_text(encoding='utf-8')
    if name=='tool_utils.py':
        before='''    context_focus_question: Optional[str] = Field(
        default=None,
        description="Optional question for context-aware pruning. Use this to filter large command outputs for relevant information. Must be a complete, self-contained question (not keywords/phrases).",
    )'''
        after='''    context_focus_question: str = Field(
        min_length=1,
        description="Required question for context-aware pruning. Use this to filter large command outputs for relevant information. Must be a complete, self-contained question (not keywords/phrases).",
    )'''
        assert text.count(before)==1
        text=text.replace(before,after)
    (dest/'runtime'/name).write_text(text,encoding='utf-8')
runner=(ROOT/'revision_precision/run_study.py').read_text(encoding='utf-8')
runner=runner.replace('runs/precision/formal','runs/hint/formal').replace('glm-precision-','glm-hint-').replace('judge-precision-','judge-hint-').replace('revision_precision/protocol.json','revision_hint/protocol.json').replace('revision_subset/runtime','revision_hint/runtime').replace("phase='artifact_aligned_fp32'","phase='required_hint_ablation'").replace("MODES=['baseline','pruner']","MODES=['pruner']")
(dest/'run_study.py').write_text(runner,encoding='utf-8')
p=json.loads((ROOT/'revision_precision/protocol.json').read_text(encoding='utf-8'))
p.update(version='required-hint-policy-v1',conditions=['pruner'],planned_cells=24,
    primary_analysis='Eight fixed question clusters. Compare the separately labeled required-hint arm to optional-hint and full arms from revision_precision at the same repeat indices. All existing stages remain visible.',
    intervention='PrunerBashAction.context_focus_question becomes a required nonempty string; description says Required. Tool executor, system/user prompts, model route, source workspace, numerical inference and scoring remain identical.',
    interpretation='Explicit policy modification / mechanism ablation. The released paper schema allows omission. This arm tests whether reliable activation restores the intended pruning behavior on the accessible provider.',
    screening='Complete all eight cells at repeat 0 before evaluating. Preserve every question and failed attempt. No selection or retries based on scores.',
    comparator='runs/precision/formal, shared full and optional-pruner controls; these controls are measured once and reuse is explicit.',
    modification_phase='This policy intervention is evaluated separately from the historical exact-observation recovery extension.')
(dest/'protocol.json').write_text(json.dumps(p,indent=2),encoding='utf-8')
freeze=(ROOT/'revision_precision/freeze.py').read_text(encoding='utf-8').replace('revision_precision/run_study.py','revision_hint/run_study.py').replace('revision_precision/protocol.json','revision_hint/protocol.json').replace('revision_subset/runtime','revision_hint/runtime').replace('runs/precision/formal','runs/hint/formal')
(dest/'freeze.py').write_text(freeze,encoding='utf-8')
analysis=(ROOT/'revision_precision/analyze.py').read_text(encoding='utf-8').replace('results/precision','results/hint').replace('revision_precision/protocol.json','revision_hint/protocol.json').replace('runs/precision/formal/','runs/hint/formal/').replace('glm-precision-','glm-hint-').replace('MODES = ["baseline", "pruner"]','MODES = ["pruner"]')
(dest/'analyze.py').write_text(analysis,encoding='utf-8')
print('Prepared separate required-hint ablation; sources not yet frozen.')
