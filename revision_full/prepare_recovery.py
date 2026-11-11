"""Freeze the original recovery extension on the corrected required-hint configuration."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
dest=ROOT/'revision_recovery';dest.mkdir(exist_ok=True)
assert not (ROOT/'runs/recovery/formal/runtime_manifest.json').exists()
for name in ['run_study.py','freeze.py','analyze.py']:
    text=(ROOT/'revision_hint'/name).read_text(encoding='utf-8')
    text=text.replace('revision_hint/','revision_recovery/').replace('runs/hint/','runs/recovery/').replace('results/hint','results/recovery').replace('glm-hint-','glm-recovery-').replace('judge-hint-','judge-recovery-')
    text=text.replace("MODES=['pruner']","MODES=['recovery']").replace('MODES = ["pruner"]','MODES = ["recovery"]')
    text=text.replace("phase='required_hint_ablation'","phase='required_hint_raw_recovery'")
    if name=='analyze.py':text=text.replace('range(3)',"range(protocol['repeats'])").replace('* 3 *',"* protocol['repeats'] *").replace('len(g) == 3',"len(g) == protocol['repeats']")
    (dest/name).write_text(text,encoding='utf-8')
(dest/'runtime').mkdir(exist_ok=True)
for name in ['main.py','tool_utils.py']:(dest/'runtime'/name).write_bytes((ROOT/'revision_hint/runtime'/name).read_bytes())
p=json.loads((ROOT/'revision_hint/protocol.json').read_text(encoding='utf-8'))
p.update(version='required-hint-recovery-v1',repeats=1,conditions=['recovery'],planned_cells=8,
    intervention='Add the existing task-local raw observation store and bounded ExpandObservation tool to the required-hint agent. The main runtime, pruning action and executor are byte-identical to revision_hint. recovery_tool.py layers storage and range retrieval over that executor.',
    comparator='Complete eight repeat0 cells from revision_hint; same fixed question set, model, source repositories, step/time limits, skimmer and judge.',
    order='Independent later execution of the same eight questions; report time-order and path variation. Protocol specified before any new recovery calls.',
    primary_analysis='Eight paired question clusters; score and total input+output tokens, expand calls, repeated lines, actual pruning and infrastructure attempts. Include all scheduled questions.',
    retry_policy='Transport recovery wrapper applies; preserve all failures and use first qualified answer regardless of score.',
    repeat_semantics='One complete eight-question diagnostic repetition; additional repetitions require a separate documented decision.',
    screening='Prioritize completion of the original-protocol and schema-matched subset; launch this extension only within available authorized budget.',
    modification_phase='Primary well-scoped extension: lossless task-local observation storage with at most 200 lines returned per expand call.')
(dest/'protocol.json').write_text(json.dumps(p,indent=2),encoding='utf-8')
# The standalone mechanism probe repeats the original predeclared eight cases.
probe=(ROOT/'revision_glm/recovery_probe.py').read_text(encoding='utf-8')
probe=probe.replace("OUT=ROOT/'runs/glm/pinned/mechanism'","OUT=ROOT/'runs/recovery/mechanism'").replace("f'mechanism-{mode}-{i}-{repeat}'","f'mechanism-fp32-{mode}-{i}-{repeat}'")
(dest/'recovery_probe.py').write_text(probe,encoding='utf-8')
an=(ROOT/'revision_glm/analyze_mechanism.py').read_text(encoding='utf-8').replace('runs/glm/pinned/mechanism','runs/recovery/mechanism').replace('results/glm','results/recovery')
(dest/'analyze_mechanism.py').write_text(an,encoding='utf-8')
out=ROOT/'runs/recovery/mechanism';out.mkdir(parents=True,exist_ok=True)
plan=json.loads((ROOT/'runs/glm/pinned/mechanism/plan.json').read_text(encoding='utf-8'))
plan.update(revision='FP32 parameter loading + original padding; same fixed cases and exact-string scoring.',previous_plan_sha256=hashlib.sha256((ROOT/'runs/glm/pinned/mechanism/plan.json').read_bytes()).hexdigest())
(out/'plan.json').write_text(json.dumps(plan,indent=2),encoding='utf-8')
print('Prepared eight recovery QA cells and the same 72 controlled mechanism cells; no paid calls.')
