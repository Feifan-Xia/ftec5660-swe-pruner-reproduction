"""Check result completeness, provider identity, score provenance and exact recovery."""

import hashlib, json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "runs/glm/pinned"
RESULTS = ROOT / "results/glm"


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def main():
    errors = []
    checks = {}
    analysis = read(RESULTS / "analysis.json")
    cells = read(RESULTS / "cells.json")
    mechanism = read(RESULTS / "mechanism.json")
    protocol = read(ROOT / "revision_glm/protocol.json")
    if not analysis["final"] or analysis["pending"] or len(cells) != 72:
        errors.append("Primary study is incomplete")
    expected = {
        (i, r, m)
        for i in protocol["question_indices"]
        for r in range(3)
        for m in protocol["conditions"]
    }
    actual = {(x["index"], x["repeat"], x["mode"]) for x in cells}
    if expected != actual or len(actual) != len(cells):
        errors.append("Primary cells differ from the planned paired inventory")
    source = (
        ROOT / "upstream/downstream_eval/multi_turn/sweqa/questions/streamlink.jsonl"
    )
    selection = read(ROOT / "configs/task_selection.json")
    snapshot = read(RESULTS / "repository_snapshot_audit.json")
    if snapshot["status"] != "PASS" or not snapshot["revision"].startswith(
        selection["repo_commit"]
    ):
        errors.append("Pinned repository snapshot verification failed")
    checks["repository_files_verified"] = snapshot["files"]
    if hashlib.sha256(source.read_bytes()).hexdigest() != selection["source_sha256"]:
        errors.append("Question source hash mismatch")
    questions = [json.loads(x) for x in source.read_text(encoding="utf-8").splitlines()]
    manifest = read(BASE / "formal/runtime_manifest.json")
    for name, expected_hash in manifest["files"].items():
        saved = BASE / "formal/frozen_source" / name
        if (
            not saved.exists()
            or hashlib.sha256(saved.read_bytes()).hexdigest() != expected_hash
        ):
            errors.append("Launch snapshot mismatch: " + name)
        if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected_hash:
            errors.append("Current runtime differs from launch: " + name)
    checks["frozen_files"] = len(manifest["files"])
    for cell in cells:
        d = ROOT / cell["path"]
        log = (d / "console.log").read_text(encoding="utf-8", errors="replace")
        if any(
            marker in log
            for marker in [
                "Pruning failed:",
                "Pruner request error",
                "Pruner request failed",
            ]
        ):
            errors.append(
                "Selected attempt contains a pruning failure: " + cell["path"]
            )
        question = [
            json.loads(x)
            for x in (d / "questions/streamlink.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ]
        if question != [{"question": questions[cell["index"]]["question"]}]:
            errors.append("Agent question input mismatch: " + cell["path"])
        if not cell["qualified"] or not cell["answered"] or cell["score"] is None:
            errors.append("Unresolved execution/scoring: " + cell["path"])
        score = read(d / "score.json")
        raw = read(d / f"judge_raw_{score['judge_attempt']}.json")
        decoded = json.loads(
            raw["choices"][0]["message"]["content"]
            .strip()
            .removeprefix("```json")
            .removesuffix("```")
        )
        if (
            decoded != score["scores"]
            or abs(sum(decoded.values()) / 5 - score["mean"]) > 1e-9
        ):
            errors.append("Score provenance mismatch: " + cell["path"])
        answers = [
            json.loads(x)
            for p in (d / "answers").rglob("*answers.jsonl")
            for x in p.read_text(encoding="utf-8").splitlines()
        ]
        if answers[-1]["token_cost"] != cell["total_tokens"]:
            errors.append("Export/meter token mismatch: " + cell["path"])
        if (d / "observations.json").exists():
            store = read(d / "observations.json")
            for oid, text in store["observations"].items():
                if oid != "obs_" + hashlib.sha256(text.encode()).hexdigest()[:16]:
                    errors.append("Observation ID mismatch: " + cell["path"])
            for record in store["reads"]:
                lines = store["observations"][record["observation_id"]].splitlines(
                    keepends=True
                )
                if (
                    not 1 <= record["start"] <= record["end"] <= len(lines)
                    or record["end"] - record["start"] >= 200
                ):
                    errors.append("Invalid recovery range: " + cell["path"])
                if (
                    len("".join(lines[record["start"] - 1 : record["end"]]))
                    != record["returned_chars"]
                ):
                    errors.append("Recovery length mismatch: " + cell["path"])
    calls = [
        json.loads(x) for x in (BASE / "formal_usage.jsonl").read_text().splitlines()
    ]
    for call in calls:
        expected_provider = "Z.AI" if call["model"] == "z-ai/glm-4.6" else "OpenAI"
        if call.get("status") == 200 and call.get("provider") != expected_provider:
            errors.append("Provider pin mismatch: " + call["request_id"])
        slug = "z-ai" if expected_provider == "Z.AI" else "openai"
        if call["parameters"].get("provider") != {
            "only": [slug],
            "allow_fallbacks": False,
        }:
            errors.append("Request provider configuration mismatch")
        if (
            call["model"] == "z-ai/glm-4.6"
            and call["parameters"].get("temperature") != 0
        ):
            errors.append("Agent temperature mismatch")
        if not (BASE / "requests" / f"{call['request_id']}.request.json").exists():
            errors.append("Missing raw request")
        if (
            call.get("status") == 200
            and not (BASE / "requests" / f"{call['request_id']}.response.txt").exists()
        ):
            errors.append("Missing successful raw response")
    checks["requests"] = len(calls)
    checks["meter_conservative_usd"] = sum(x["cost"] for x in calls)
    checks["known_provider_cost_usd"] = sum(
        x["cost"] for x in calls if x["cost_kind"] == "provider_reported"
    )
    checks["unreconciled_requests"] = sum(
        x["cost_kind"] != "provider_reported" for x in calls
    )
    auth = read(BASE / "budget_authorization.json")
    checks["project_conservative_usd"] = (
        auth["legacy_conservative"]
        + auth["glm_development"]
        + auth["mixed_route_audit"]
        + auth["judge_probe"]
        + checks["meter_conservative_usd"]
        + auth["connectivity_and_unsettled_margin"]
    )
    if checks["project_conservative_usd"] > auth["approved_total_usd"] + 1e-6:
        errors.append("Approved total budget exceeded")
    if not mechanism["final"] or mechanism["n"] != 72 or mechanism["pending"]:
        errors.append("Mechanism study incomplete")
    for i in range(8):
        case = read(BASE / f"mechanism/case{i}.json")
        if hashlib.sha256(case["source"].encode()).hexdigest() != case["source_sha256"]:
            errors.append("Mechanism source mismatch")
        original = (ROOT / "data/streamlink" / case["path"]).read_text(encoding="utf-8")
        if original != case["source"]:
            errors.append("Mechanism fixture differs from the pinned repository")
        for mode in ["full", "pruned", "recoverable"]:
            for repeat in range(3):
                result = read(BASE / f"mechanism/{mode}/case{i}_r{repeat}.json")
                try:
                    answer = json.loads(
                        result["answer"]
                        .strip()
                        .removeprefix("```json")
                        .removesuffix("```")
                    )
                except ValueError:
                    answer = None
                if result["correct"] != (answer == case["expected"]):
                    errors.append("Exact-match score mismatch")
                for record in result["reads"]:
                    recovered = "".join(
                        case["source"].splitlines(keepends=True)[
                            record["start"] - 1 : record["end"]
                        ]
                    )
                    if len(recovered) != record["returned_chars"]:
                        errors.append("Mechanism recovery length mismatch")
    checks["primary_cells"] = len(cells)
    checks["mechanism_cells"] = mechanism["n"]
    output = {
        "errors": errors,
        "checks": checks,
        "experiment_commit": manifest["git_revision"],
        "status": "PASS" if not errors else "FAIL",
    }
    (RESULTS / "audit.json").write_text(json.dumps(output, indent=2), encoding="utf-8")
    print(json.dumps(output, indent=2))
    if errors:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
