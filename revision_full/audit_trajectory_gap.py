"""Trace-level gap audit: all fixed questions, explicit references, no API calls."""
import collections
import json
import statistics
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def inspect(t):
    events = t["events"]
    actions = [e.get("action", {}) for e in events if e["type"] == "ActionEvent"]
    commands = [a["command"] for a in actions if a.get("command")]
    observations = [e["observation"] for e in events if e.get("observation")]
    def text(o):
        return o.get("original_output") or o.get("output") or str(o.get("content", ""))
    timeouts = [{"event": n, "command": next((p.get("action", {}).get("command") for p in reversed(events[:n]) if p.get("action", {}).get("command")), None), "text": text(e["observation"])}
                for n, e in enumerate(events) if e.get("observation") and "Error: Command timed out after 10 seconds" in text(e["observation"])]
    errors = [{"event": n, "error": e.get("error")} for n, e in enumerate(events) if e["type"] == "AgentErrorEvent"]
    bash = [a for a in actions if a.get("command")]
    return {"bash_actions": len(bash), "action_events": len(actions),
            "hint_actions": sum(bool(a.get("context_focus_question")) for a in bash),
            "timeout_observations": len(timeouts), "timeout_evidence": timeouts,
            "agent_errors": len(errors), "error_evidence": errors,
            "duplicate_commands": sum(v - 1 for v in collections.Counter(commands).values()),
            "raw_observation_chars": sum(len(text(o)) for o in observations),
            "prune_calls": sum(bool(o.get("pruned")) for o in observations),
            "first_commands": commands[:5], "all_commands": commands,
            "has_finish_action": any(a.get("kind") == "FinishAction" for a in actions)}


def main():
    questions = [json.loads(s)["question"] for s in (ROOT / "upstream/downstream_eval/multi_turn/sweqa/questions/streamlink.jsonl").read_text(encoding="utf-8").splitlines()]
    indices = read(ROOT / "revision_precision/protocol.json")["question_indices"]
    rows = []
    with zipfile.ZipFile(ROOT / "runs/author_evidence/swepruner-sweqa-reproduce.zip") as z:
        for mode, folder in [("baseline", "traj-full-glm"), ("pruner", "traj-full-glm-pruner")]:
            for member in z.namelist():
                if not (member.startswith(folder + "/streamlink/") and member.endswith(".traj.json")):
                    continue
                t = json.loads(z.read(member)); index = questions.index(t["question"])
                if index in indices:
                    rows.append(dict(source="author", index=index, mode=mode, repeat=0, path=member, **inspect(t)))
    cells = read(ROOT / "results/precision/cells.json")
    for c in cells:
        p = ROOT / c["path"]
        paths = list((p / "trajectories/streamlink").glob("*.traj.json")); assert len(paths) == 1
        rows.append(dict(source="local", index=c["index"], mode=c["mode"], repeat=c["repeat"], path=str(paths[0].relative_to(ROOT)), **inspect(read(paths[0]))))
    metrics = ["bash_actions", "action_events", "hint_actions", "timeout_observations", "agent_errors", "duplicate_commands", "raw_observation_chars", "prune_calls"]
    groups = {}
    for source in ["author", "local"]:
        for mode in ["baseline", "pruner"]:
            group = [r for r in rows if r["source"] == source and r["mode"] == mode]
            groups[source + "_" + mode] = dict(tasks=len(group), means={k: statistics.mean(r[k] for r in group) for k in metrics},
                totals={k: sum(r[k] for r in group) for k in metrics},
                timeout_tasks=sum(r["timeout_observations"] > 0 for r in group),
                hint_action_percent=100 * sum(r["hint_actions"] for r in group) / sum(r["bash_actions"] for r in group))
    by_question = []
    for i in indices:
        pair = {m: [c for c in cells if c["index"] == i and c["mode"] == m] for m in ["baseline", "pruner"]}
        by_question.append({"index": i, "token_saving": statistics.mean(c["total_tokens"] for c in pair["baseline"]) - statistics.mean(c["total_tokens"] for c in pair["pruner"]),
            "prune_calls": sum(c["prune_calls"] for c in pair["pruner"])})
    full = [c for c in cells if c["mode"] == "baseline"]; pruned = [c for c in cells if c["mode"] == "pruner"]
    bt = sum(c["total_tokens"] for c in full); pt = sum(c["total_tokens"] for c in pruned)
    bc = sum(c["api_requests"] for c in full); pc = sum(c["api_requests"] for c in pruned)
    factorization = {"request_count_change_percent": 100 * (pc / bc - 1), "tokens_per_request_change_percent": 100 * ((pt / pc) / (bt / bc) - 1), "total_tokens_change_percent": 100 * (pt / bt - 1),
                     "interpretation": "Exact aggregate arithmetic. Independent online paths and tool contracts vary; this decomposition does not identify a causal pruning effect."}
    out = dict(question_indices=indices, groups=groups, local_token_factorization=factorization, local_question_saving=by_question, records=rows)
    (ROOT / "results/full/trajectory_gap_audit.json").write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"groups": groups, "factorization": factorization, "question_saving": by_question}, indent=2))


if __name__ == "__main__":
    main()
