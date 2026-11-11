"""Audit priming's actual wire boundary and apply its frozen development gate."""
import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    cells = read(ROOT / "results/priming/cells.json")
    protocol = read(ROOT / "revision_priming/protocol.json")
    assert len(cells) == protocol["planned_cells"]
    ledger = [json.loads(s) for s in (ROOT / "runs/full/formal_usage.jsonl").read_text(encoding="utf-8").splitlines()]
    rows = []
    for c in cells:
        session = f'glm-priming-{c["mode"]}-{c["index"]}-{c["repeat"]}-a{c["attempt"]}'
        calls = [r for r in ledger if r["session"] == session]
        bodies = [read(ROOT / "runs/full/requests" / (r["request_id"] + ".request.json"))["body"] for r in calls]
        native = [b for b in bodies if b.get("tools")]
        assert len(native) >= 2
        params = [next(t for t in b["tools"] if t["function"]["name"] == "pruner_bash")["function"]["parameters"] for b in native]
        assert "context_focus_question" in params[0]["required"]
        assert params[0]["properties"]["context_focus_question"]["minLength"] == 1
        assert all("context_focus_question" not in p["required"] and "minLength" not in p["properties"]["context_focus_question"] for p in params[1:])
        first_message = next(m for m in native[1]["messages"] if m["role"] == "assistant" and m.get("tool_calls"))
        first_bash = sum(t["function"]["name"] == "pruner_bash" for t in first_message["tool_calls"])
        traj = read(next((ROOT / c["path"] / "trajectories/streamlink").glob("*.traj.json")))
        actions = [e["action"] for e in traj["events"] if e.get("action", {}).get("command")]
        later_hints = sum(bool(a.get("context_focus_question")) for a in actions[first_bash:])
        rows.append(dict(c, primed_bash_actions=first_bash, later_hint_actions=later_hints, wire_priming_verified=True))
    groups = {}
    for mode in ["baseline", "pruner"]:
        group = [r for r in rows if r["mode"] == mode]
        groups[mode] = {"n": len(group), **{k: statistics.mean(r[k] for r in group) for k in ["total_tokens", "score", "api_requests", "prune_calls"]},
            "later_hint_tasks": sum(r["later_hint_actions"] > 0 for r in group), "later_hint_actions": sum(r["later_hint_actions"] for r in group)}
    changes = {k: 100 * (groups["pruner"][k] / groups["baseline"][k] - 1) for k in ["total_tokens", "score", "api_requests"]}
    gate = groups["pruner"]["later_hint_tasks"] >= 2 and changes["total_tokens"] < 0 and changes["score"] >= -2
    out = {"protocol": "revision_priming/protocol.json", "groups": groups, "changes_percent": changes, "go_gate_passed": gate, "rows": rows,
        "scope": "Three development questions, one execution per condition, matched tools and first-request priming. Serving-policy adaptation; original fixed-eight reproduction remains separately reported."}
    (ROOT / "results/full/priming_development.json").write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in out.items() if k != "rows"}, indent=2))


if __name__ == "__main__":
    main()
