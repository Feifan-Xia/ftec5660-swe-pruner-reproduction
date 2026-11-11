"""Isolate first-action hint presence with identical raw observation and schema."""
import copy
import json
import zipfile
from pathlib import Path

import probe_explicit_hint_decision as probe

ROOT = Path(__file__).resolve().parents[1]
probe.OUT = ROOT / "runs/full/diagnostics/hint_history"
probe.OUT.mkdir(parents=True, exist_ok=True)
protocol = {"version": 1, "development_indices": [43, 26, 17], "requests": 6,
    "contrast": "Identical author first command, its unchanged output, original optional schema, system and user. Only presence of the author's first-action context_focus_question differs.",
    "metric": "Nonempty hint in the next model-generated Bash action.",
    "go_gate": "At least two of three with-hint continuations produce hints and exceed the without-hint count. A pass supports a separate first-request-priming pilot, not a claim about original gateway internals.",
    "selection": "Use all three development questions from previous probes, distinct from the fixed eight evaluation questions.",
    "budget": "Within existing USD12 total; expected below USD0.02."}
target = probe.OUT / "protocol.json"
if target.exists(): assert json.loads(target.read_text(encoding="utf-8")) == protocol
else: target.write_text(json.dumps(protocol, indent=2), encoding="utf-8")
questions = [json.loads(s)["question"] for s in (ROOT / "upstream/downstream_eval/multi_turn/sweqa/questions/streamlink.jsonl").read_text(encoding="utf-8").splitlines()]
jobs = []
with zipfile.ZipFile(ROOT / "runs/author_evidence/swepruner-sweqa-reproduce.zip") as z:
    ts = {t["question"]: (name, t) for name in z.namelist() if name.startswith("traj-full-glm-pruner/streamlink/") and name.endswith(".traj.json") for t in [json.loads(z.read(name))]}
    for index in protocol["development_indices"]:
        member, t = ts[questions[index]]
        system = next(e for e in t["events"] if e["type"] == "SystemPromptEvent")
        user = next(e for e in t["events"] if e["type"] == "MessageEvent" and e.get("source") == "user")
        action = next(e["action"] for e in t["events"] if e.get("action", {}).get("command"))
        obs = next(e["observation"] for e in t["events"] if e.get("observation"))
        assert obs["original_output"] == obs["output"], "Use exactly equal initial observations"
        for variant in ["without_hint", "with_hint"]:
            arguments = {"command": action["command"], "security_risk": "LOW"}
            if variant == "with_hint": arguments["context_focus_question"] = action["context_focus_question"]
            messages = [{"role": "system", "content": system["system_prompt"]["text"]}, {"role": "user", "content": user["content"]},
                {"role": "assistant", "content": None, "tool_calls": [{"id": "fixture_initial", "type": "function", "function": {"name": "pruner_bash", "arguments": json.dumps(arguments)}}]},
                {"role": "tool", "tool_call_id": "fixture_initial", "content": "Raw Output: \n" + obs["original_output"]}]
            body = {"model": "z-ai/glm-4.6", "temperature": 0, "top_p": 1, "messages": messages, "tools": copy.deepcopy(system["tools"])}
            plan = {"index": index, "prefix": "one_author_action", "variant": variant, "source_member": member, "body": body}
            name = f"q{index}-{variant}"; path = probe.OUT / (name + ".plan.json")
            if path.exists(): assert json.loads(path.read_text(encoding="utf-8")) == plan
            else: path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
            jobs.append((name, plan))
with probe.concurrent.futures.ThreadPoolExecutor(3) as pool:
    rows = list(pool.map(probe.execute, jobs))
counts = {v: sum(r["has_hint"] for r in rows if r["variant"] == v) for v in protocol.get("variants", ["with_hint", "without_hint"])}
out = {"rows": rows, "counts": counts, "go_gate_passed": counts["with_hint"] >= 2 and counts["with_hint"] > counts["without_hint"]}
(ROOT / "results/full/hint_history_probe.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=2))
