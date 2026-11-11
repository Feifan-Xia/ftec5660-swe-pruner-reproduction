"""Development-only paired schema probe: explicit hint with empty-string escape."""
import concurrent.futures
import copy
import hashlib
import json
import time
import zipfile
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "runs/full/diagnostics/explicit_hint"


def prepare():
    OUT.mkdir(parents=True, exist_ok=True)
    protocol = {"version": 1, "development_indices": [43, 26, 17], "variants": ["optional", "required_allow_empty"],
        "prefixes": ["initial", "before_first_cat"], "requests": 12,
        "intervention": "Append context_focus_question to required fields only. Keep its original string type, descriptions, and all other fields. Empty string remains valid and disables filtering.",
        "prefix_construction": "Initial author system/user/tool definitions. For before_first_cat, replay author preceding Bash commands with hints omitted and original raw outputs. Same prefix in both variants. No tool execution or reference answer exposure.",
        "go_gate": "Required-allow-empty: at least two of three before-cat responses contain a nonempty hint; at least two of three initial responses choose empty or omitted hint. Otherwise report failed transfer and do not launch a full fixed-eight study of this candidate.",
        "interpretation": "Schema-policy compatibility diagnostic. Released schema allows omission; original provider internals are unknown. This is an explicit adaptation, separately labeled from exact-contract reproduction.",
        "budget": "Within existing USD12 total. Estimated below USD0.05; shared meter hard cap applies.",
        "retry": "At most one transport/receipt recovery; preserve failed responses. No result-dependent retries."}
    target = OUT / "protocol.json"
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
            initial = [{"role": "system", "content": system["system_prompt"]["text"]}, {"role": "user", "content": user["content"]}]
            prefix = copy.deepcopy(initial); pending = None
            for n, e in enumerate(t["events"]):
                a = e.get("action", {})
                if a.get("command"):
                    if a["command"].startswith("cat "):
                        assert pending is None
                        break
                    assert pending is None
                    pending = f"fixture_{index}_{n}"
                    prefix.append({"role": "assistant", "content": None, "tool_calls": [{"id": pending, "type": "function", "function": {"name": "pruner_bash", "arguments": json.dumps({"command": a["command"], "security_risk": "LOW"})}}]})
                o = e.get("observation", {})
                if o and pending:
                    prefix.append({"role": "tool", "tool_call_id": pending, "content": "Raw Output: \n" + o["original_output"]})
                    pending = None
            assert len(prefix) > 2
            for stage, messages in [("initial", initial), ("before_first_cat", prefix)]:
                for variant in protocol["variants"]:
                    tools = copy.deepcopy(system["tools"])
                    if variant == "required_allow_empty":
                        params = tools[0]["function"]["parameters"]
                        assert "context_focus_question" not in params["required"]
                        params["required"].append("context_focus_question")
                        assert "minLength" not in params["properties"]["context_focus_question"]
                    body = {"model": "z-ai/glm-4.6", "temperature": 0, "top_p": 1, "messages": messages, "tools": tools}
                    name = f"q{index}-{stage}-{variant}"
                    plan = {"index": index, "prefix": stage, "variant": variant, "source_member": member, "body": body}
                    path = OUT / (name + ".plan.json")
                    if path.exists(): assert json.loads(path.read_text(encoding="utf-8")) == plan
                    else: path.write_text(json.dumps(plan, ensure_ascii=False, indent=2), encoding="utf-8")
                    jobs.append((name, plan))
    return jobs


def execute(job):
    name, plan = job
    target = OUT / (name + ".result.json")
    if target.exists(): return json.loads(target.read_text(encoding="utf-8"))
    payload = None
    for attempt in range(2):
        raw = OUT / f"{name}.response{attempt}.json"
        fail = OUT / f"{name}.failure{attempt}.json"
        if fail.exists(): continue
        if raw.exists(): payload = json.loads(raw.read_text(encoding="utf-8"))
        else:
            try:
                r = httpx.post("http://127.0.0.1:8879/v1/chat/completions", trust_env=False, timeout=260, headers={"x-opencode-session": f"explicit-hint-{name}-a{attempt}"}, json=plan["body"])
                r.raise_for_status(); payload = r.json()
                raw.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            except Exception as exc:
                fail.write_text(json.dumps({"time": time.time(), "error": type(exc).__name__, "detail": str(exc)}, indent=2), encoding="utf-8")
                raise
        if payload.get("usage") and payload.get("choices"): break
        raise RuntimeError("Response incomplete; inspect immutable receipt")
    assert payload is not None
    calls = [{"name": c["function"]["name"], "arguments": json.loads(c["function"]["arguments"])} for c in payload["choices"][0]["message"].get("tool_calls", [])]
    row = {k: plan[k] for k in ["index", "prefix", "variant", "source_member"]}
    bash = [c for c in calls if c["name"] == "pruner_bash"]
    row.update(tool_calls=calls, has_hint=any(c["arguments"].get("context_focus_question") for c in bash),
               all_bash_empty=bool(bash) and all(not c["arguments"].get("context_focus_question") for c in bash), usage=payload["usage"])
    target.write_text(json.dumps(row, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(row, ensure_ascii=False), flush=True)
    return row


if __name__ == "__main__":
    jobs = prepare()
    with concurrent.futures.ThreadPoolExecutor(3) as pool:
        rows = list(pool.map(execute, jobs))
    large = sum(r["has_hint"] for r in rows if r["variant"] == "required_allow_empty" and r["prefix"] == "before_first_cat")
    small = sum(r["all_bash_empty"] for r in rows if r["variant"] == "required_allow_empty" and r["prefix"] == "initial")
    result = {"rows": rows, "before_cat_with_hint": large, "initial_without_hint": small, "go_gate_passed": large >= 2 and small >= 2}
    (ROOT / "results/full/explicit_hint_probe.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in result.items() if k != "rows"}, indent=2))
