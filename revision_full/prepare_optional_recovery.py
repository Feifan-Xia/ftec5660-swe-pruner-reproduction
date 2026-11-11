"""Freeze recovery under the original optional-hint contract before paid trials."""
import json
from pathlib import Path
from fix_terminal_history import patch_runtime

ROOT=Path(__file__).resolve().parents[1]
dest=ROOT/'revision_optional'
assert not (ROOT/'runs/optional/formal/runtime_manifest.json').exists()
dest.mkdir(exist_ok=True)
for name in ['run_study.py','freeze.py','analyze.py']:
    text=(ROOT/'revision_recovery'/name).read_text(encoding='utf-8')
    text=text.replace('revision_recovery/','revision_optional/').replace('runs/recovery/','runs/optional/').replace('results/recovery','results/optional').replace('glm-recovery-','glm-optional-').replace('judge-recovery-','judge-optional-')
    text=text.replace('required_hint_raw_recovery','original_optional_hint_recovery')
    text=text.replace("FILES=[", "FILES=['revision_full/fix_terminal_history.py',") if name=='freeze.py' else text
    text=text.replace('fixed subset target is 48','fixed subset target is 24')
    (dest/name).write_text(text,encoding='utf-8')
patch_runtime(ROOT/'revision_subset/runtime/main.py',dest/'runtime/main.py')
(dest/'runtime/tool_utils.py').write_bytes((ROOT/'revision_subset/runtime/tool_utils.py').read_bytes())
p=json.loads((ROOT/'revision_precision/protocol.json').read_text(encoding='utf-8'))
p.update(version='original-optional-hint-recovery-v1',conditions=['recovery'],planned_cells=24,
    intervention='Add existing task-local raw storage and bounded line recovery under the original optional-hint tool contract. Fix terminal-summary serialization to preserve agent-visible observations.',
    comparator='All 24 original optional-hint pruner cells from revision_precision. No selected pruner trajectory used the broken terminal-summary branch, so its repair does not alter that comparator.',
    primary_analysis='Eight paired question clusters, three repetitions per question and condition. Question-cluster bootstrap 10000 resamples, seed 5660. Include all tasks and retain infrastructure failures.',
    order='Later sequential stage after the original 48-cell study; timing and path variability are limitations. Same fixed eight questions; no question replacement or outcome-dependent repetition.',
    repeat_semantics='Complete three repetitions for every fixed question, regardless of effect direction.',
    terminal_generation='Native action generation temperature 0; terminal fallback temperature 0.3. Repair serialization only, preserve template and other parameters.',
    scope_change='Subset-first steering remains active. Complete a fair original-contract modification study before deciding population expansion. Existing USD12 ceiling applies.',
    budget='Expected incremental agent+judge cost about USD0.9 based on the completed required-recovery screen; bounded by the existing shared project meter.',
    expected_behavior='Test whether optional recovery improves answer quality or reduces repeated retrieval, and measure its token/latency overhead without conditioning inclusion on improvement.')
(dest/'protocol.json').write_text(json.dumps(p,indent=2),encoding='utf-8')
print('Prepared original-contract recovery: 8 questions x 3 repetitions, 24 cells.')
