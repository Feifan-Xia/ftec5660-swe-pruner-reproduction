"""Freeze development pilot for first-request-only schema priming."""
import ast
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
dest = ROOT / "revision_priming"
assert not (ROOT / "runs/priming/formal/runtime_manifest.json").exists()
probe = json.loads((ROOT / "results/full/hint_history_probe.json").read_text(encoding="utf-8"))
assert probe["go_gate_passed"]
(dest / "runtime").mkdir(parents=True, exist_ok=True)
main = (ROOT / "revision_optional/runtime/main.py").read_text(encoding="utf-8")
(dest / "runtime/main.py").write_text("from revision_priming.prime import install\ninstall()\n" + main, encoding="utf-8")
source = (ROOT / "revision_subset/runtime/tool_utils.py").read_text(encoding="utf-8")
old = "if action.context_focus_question:"
assert source.count(old) == 1
changed = source.replace(old, 'if action.context_focus_question and os.environ.get("FTEC_DISABLE_PRUNER") != "1":')
ast.parse(changed)
(dest / "runtime/tool_utils.py").write_text(changed, encoding="utf-8")
for name in ["run_study.py", "freeze.py", "analyze.py"]:
    value = (ROOT / "revision_precision" / name).read_text(encoding="utf-8")
    for old, new in [("revision_precision/", "revision_priming/"), ("revision_subset/runtime", "revision_priming/runtime"), ("runs/precision/", "runs/priming/"), ("results/precision", "results/priming"), ("glm-precision-", "glm-priming-"), ("judge-precision-", "judge-priming-")]:
        value = value.replace(old, new)
    if name == "run_study.py":
        value = value.replace("EXPERIMENT_TYPE=mode,", "EXPERIMENT_TYPE='pruner',FTEC_DISABLE_PRUNER='1' if mode=='baseline' else '0',")
        value = value.replace("phase='", "phase='priming_development_")
        value = value.replace("fixed subset target is 48", "development pilot target is 6")
    if name == "freeze.py":
        value = value.replace("FILES=[", "FILES=['revision_priming/prime.py','revision_full/fix_terminal_history.py',")
    if name == "analyze.py":
        value = value.replace("range(3)", "range(protocol['repeats'])").replace("* 3 *", "* protocol['repeats'] *").replace("len(g) == 3", "len(g) == protocol['repeats']")
    (dest / name).write_text(value, encoding="utf-8")
protocol = json.loads((ROOT / "revision_precision/protocol.json").read_text(encoding="utf-8"))
protocol.update(version="first-request-priming-development-v1", question_indices=[43, 26, 17], population_size=3, repeats=1, planned_cells=6,
    population="Three existing development questions; disjoint from fixed eight reported subset. All six balanced cells retained.",
    intervention="Only first native API request requires a nonempty hint. Every later request restores the original optional field, allowing unfiltered rereads. No author commands, outputs, answers, or hints enter live execution.",
    comparator="Matched full-output control uses identical schemas, first-request priming, system/user prompts, terminal repair and model. Only the executor's filtering branch differs.",
    primary_analysis="All three paired questions, one execution each, descriptive development screen. No outcome-based retries or question replacement.",
    order="Alternate full/pruner by question index ordinal. Two workers maximum; matched controls use fresh executions.",
    repeat_semantics="Exactly one development repetition. Further fixed-eight confirmation needs a separately frozen protocol and all three repetitions.",
    scope_change="User requests small-scope alignment first; full48 expansion deferred. Approved project ceiling remains USD12.",
    screening="Proceed to fixed-eight confirmation only if at least two of three pruner tasks activate after their first API request, paired aggregate tokens decline, and mean quality decline is at most 2% relative. Otherwise retain the candidate as failed diagnostic. These thresholds are set before this pilot.",
    target="Working small-scope confirmation target: at least 40% end-to-end token reduction (within 10 percentage points of author same-eight 49.9%) with mean quality decline at most 2%. Report cluster uncertainty and all three repeats. This is an engineering target, not a guaranteed outcome.",
    interpretation="Serving-policy adaptation, separate from exact-contract reproduction and raw-observation recovery modification. Gateway internals remain unknown.",
    budget="Estimated USD0.2-0.3 development pilot inside USD12. No full48 expansion or extra approval assumed.")
(dest / "protocol.json").write_text(json.dumps(protocol, indent=2), encoding="utf-8")
print("Prepared 6-cell development pilot; source not frozen or run yet.")
