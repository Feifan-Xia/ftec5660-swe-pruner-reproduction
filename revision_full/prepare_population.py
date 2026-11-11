"""Prepare the remaining 40 questions without making API calls."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
dest=ROOT/'revision_population';dest.mkdir(exist_ok=True)
assert not (ROOT/'runs/population/formal/runtime_manifest.json').exists()
for name in ['run_study.py','freeze.py','analyze.py']:
    text=(ROOT/'revision_optional'/name).read_text(encoding='utf-8')
    text=text.replace('revision_optional/','revision_population/').replace('runs/optional/','runs/population/').replace('results/optional','results/population').replace('glm-optional-','glm-population-').replace('judge-optional-','judge-population-')
    text=text.replace("MODES=['recovery']","MODES=['baseline','pruner','recovery']").replace('MODES = ["recovery"]','MODES = ["baseline", "pruner", "recovery"]')
    text=text.replace('if args.include_recovery:', 'if args.include_recovery and "recovery" not in MODES:')
    text=text.replace('original_optional_hint_recovery','remaining_streamlink_population')
    text=text.replace('fixed subset target is 24','remaining population target is 360')
    (dest/name).write_text(text,encoding='utf-8')
(dest/'runtime').mkdir(exist_ok=True)
for name in ['main.py','tool_utils.py']:(dest/'runtime'/name).write_bytes((ROOT/'revision_optional/runtime'/name).read_bytes())
p=json.loads((ROOT/'revision_optional/protocol.json').read_text(encoding='utf-8'))
subset=p['question_indices'];p.update(version='streamlink-remaining40-v1',question_indices=[i for i in range(48) if i not in subset],population_size=40,conditions=['baseline','pruner','recovery'],planned_cells=360,
    full_population=48,existing_subset_indices=subset,existing_subset_cells=72,
    population='Every remaining question from the released 48-question Streamlink file. Combine with all fixed-eight three-repetition cells, retaining stage identifiers.',
    intervention='Original optional-hint SWE-Pruner and task-local raw recovery, with the same corrected terminal serializer in every newly executed condition.',
    comparator='Within-question full, optional pruner and optional recovery, each with three repeats. Existing subset full terminal replay is separately identified.',
    primary_analysis='Complete 48-question population x three repeats x three conditions, 432 cells including earlier subset. Paired question-cluster bootstrap over all48 with all3repeats retained; stage sensitivity and failure records separately reported.',
    order='Remaining question indices ascending; within each question and repeat, rotate condition order by question ordinal plus repeat. Fixed subset was executed earlier; retain stage and time-order limitations.',
    repeat_semantics='Complete all three planned repetitions without outcome-dependent stopping or question replacement.',
    scope_change='Prepared for requested full Streamlink expansion. Launch requires completion of optional subset and explicit sufficient budget authorization.',
    budget='Estimated additional Agent+judge USD12.3 for360 cells. Proposed project capUSD24 is pending; current approved ceiling remainsUSD12.',
    expected_behavior='Measure the full-population effect and uncertainty regardless of sign. Preserve all failures and subgroup variation.')
(dest/'protocol.json').write_text(json.dumps(p,indent=2),encoding='utf-8')
print('Prepared360 future cells; no calls made, no authorization changed.')
