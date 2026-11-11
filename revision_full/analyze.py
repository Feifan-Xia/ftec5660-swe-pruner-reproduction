"""Produce traceable paired statistics for every planned GLM cell."""

import argparse, json, statistics, random, csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "results/full"
OUT.mkdir(parents=True, exist_ok=True)
MODES = ["baseline", "pruner"]


def read(p, default=None):
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else default


def mean(xs):
    return statistics.mean(xs) if xs else None


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--partial", action="store_true")
    parser.add_argument("--include-recovery", action="store_true")
    args = parser.parse_args()
    if args.include_recovery:
        MODES.append("recovery")
    protocol = read(ROOT / "revision_full/protocol.json")
    ledger = ROOT / "runs/full/formal_usage.jsonl"
    calls = (
        [json.loads(x) for x in ledger.read_text(encoding="utf-8").splitlines()]
        if ledger.exists()
        else []
    )
    rows = []
    attempts = []
    pending = []
    for index in protocol["question_indices"]:
        for repeat in range(3):
            for mode in MODES:
                base = ROOT / f"runs/full/formal/{mode}/q{index}_r{repeat}"
                selection = read(base / "selection.json")
                selected = selection.get("selected_attempt") if selection else None
                if selection is None:
                    pending.append([index, repeat, mode])
                for p in sorted(base.glob("attempt*/task.json")):
                    task = read(p)
                    d = p.parent
                    a = task["attempt"]
                    session = f"glm-full-{mode}-{index}-{repeat}-a{a}"
                    req = [x for x in calls if x["session"] == session]
                    usage = [x.get("usage", {}) for x in req]
                    answers = [
                        json.loads(x)
                        for f in (d / "answers").rglob("*answers.jsonl")
                        for x in f.read_text(encoding="utf-8").splitlines()
                        if x.strip()
                    ]
                    answer = answers[-1] if answers else {}
                    score = read(d / "score.json", {})
                    qual = read(d / "qualification.json", {})
                    traj = [
                        read(f)
                        for f in (d / "trajectories/streamlink").glob("*.traj.json")
                    ]
                    events = [e for t in traj for e in t["events"]]
                    observations = [
                        e.get("observation", {})
                        for e in events
                        if e.get("type") == "ObservationEvent"
                    ]
                    pruned = [o for o in observations if o.get("pruned")]
                    store = read(d / "observations.json", {})
                    reads = store.get("reads", [])
                    actions = [
                        e.get("action", {})
                        for e in events
                        if e.get("type") == "ActionEvent"
                    ]
                    commands = [a["command"] for a in actions if "command" in a]
                    row = {
                        "index": index,
                        "repeat": repeat,
                        "mode": mode,
                        "attempt": a,
                        "path": d.relative_to(ROOT).as_posix(),
                        "qualified": qual.get("qualified", False),
                        "failure_reasons": qual.get("reasons", []),
                        "answered": bool(answer.get("answer", "").strip())
                        and answer.get("answer") != "No answer found",
                        "score": score.get("mean"),
                        "dimensions": score.get("scores"),
                        "author_filtered_eligible": score.get(
                            "author_filtered_eligible"
                        ),
                        "input_tokens": sum(u.get("prompt_tokens", 0) for u in usage),
                        "output_tokens": sum(
                            u.get("completion_tokens", 0) for u in usage
                        ),
                        "cached_tokens": sum(
                            u.get("prompt_tokens_details", {}).get("cached_tokens", 0)
                            for u in usage
                        ),
                        "reasoning_tokens": sum(
                            u.get("completion_tokens_details", {}).get(
                                "reasoning_tokens", 0
                            )
                            for u in usage
                        ),
                        "api_requests": len(req),
                        "author_rounds": sum(
                            e.get("source") in ["agent", "user"] for e in events
                        ),
                        "tool_actions": len(actions),
                        "seconds": answer.get("time_cost"),
                        "cost": sum(r["cost"] for r in req),
                        "prune_calls": len(pruned),
                        "raw_pruned_tokens": sum(
                            o.get("prune_info", {}).get("origin_token_cnt", 0) or 0
                            for o in pruned
                        ),
                        "kept_pruned_tokens": sum(
                            o.get("prune_info", {}).get("left_token_cnt", 0) or 0
                            for o in pruned
                        ),
                        "expand_calls": len(reads),
                        "expanded_chars": sum(r["returned_chars"] for r in reads),
                        "repeated_lines": sum(r["repeated_lines"] for r in reads),
                        "repeated_exact_commands": len(commands) - len(set(commands)),
                        "tool_timeout_observations": sum(
                            "Error: Command timed out"
                            in str(o.get("output", o.get("content", "")))
                            for o in observations
                        ),
                        "max_input_tokens": max(
                            [u.get("prompt_tokens", 0) for u in usage], default=0
                        ),
                        "providers": sorted(
                            {r.get("provider") for r in req if r.get("provider")}
                        ),
                    }
                    row["expand_tool_actions"] = sum(
                        x.get("kind") == "ExpandAction" for x in actions
                    )
                    row["conservative_cost"] = row["cost"]
                    row["cost"] = sum(
                        r["cost"] for r in req if r["cost_kind"] == "provider_reported"
                    )
                    row["stored_observation_bytes"] = sum(
                        len(text.encode("utf-8"))
                        for text in store.get("observations", {}).values()
                    )
                    row["stored_observations"] = len(store.get("observations", {}))
                    row["total_tokens"] = row["input_tokens"] + row["output_tokens"]
                    attempts.append(row)
                    if a == selected:
                        rows.append(row)
                if selection and selected is None:
                    last = next(
                        (
                            r.copy()
                            for r in reversed(attempts)
                            if r["index"] == index
                            and r["repeat"] == repeat
                            and r["mode"] == mode
                        ),
                        None,
                    )
                    if last:
                        rows.append(last)
    summary = {
        "planned": len(protocol["question_indices"]) * 3 * len(MODES),
        "pending": pending,
        "selected_cells": len(rows),
        "attempts": len(attempts),
        "final": not args.partial,
        "conditions": {},
        "paired": {},
        "first_attempt": {},
    }
    if not args.partial:
        assert (
            not pending and len(rows) == len(protocol["question_indices"]) * 3 * len(MODES)
        ), "All scheduled cells must have a resolved selection"
        assert all(
            not r["answered"] or r["score"] is not None for r in rows
        ), "Every answer must be scored"
    for key, pop in [
        ("conditions", rows),
        ("first_attempt", [r for r in attempts if r["attempt"] == 0]),
    ]:
        for mode in MODES:
            g = [r for r in pop if r["mode"] == mode]
            scores = [r["score"] for r in g if r["score"] is not None]
            summary[key][mode] = {
                "n": len(g),
                "answered": sum(r["answered"] for r in g),
                "qualified": sum(r["qualified"] for r in g),
                "scored": len(scores),
                "mean_score": mean(scores),
                "failure_zero_score": mean(
                    [r["score"] if r["score"] is not None else 0 for r in g]
                ),
                "pruning_tasks": sum(r["prune_calls"] > 0 for r in g),
                "expansion_tasks": sum(r["expand_calls"] > 0 for r in g),
            }
            for metric in [
                "total_tokens",
                "input_tokens",
                "output_tokens",
                "cached_tokens",
                "api_requests",
                "author_rounds",
                "seconds",
                "max_input_tokens",
            ]:
                summary[key][mode]["mean_" + metric] = mean(
                    [r[metric] for r in g if r[metric] is not None]
                )
            for metric in [
                "cost",
                "conservative_cost",
                "stored_observation_bytes",
                "stored_observations",
                "prune_calls",
                "raw_pruned_tokens",
                "kept_pruned_tokens",
                "expand_calls",
                "expand_tool_actions",
                "expanded_chars",
                "repeated_lines",
                "repeated_exact_commands",
                "tool_timeout_observations",
            ]:
                summary[key][mode]["sum_" + metric] = sum(r[metric] for r in g)
            summary[key][mode]["median_total_tokens"] = (
                statistics.median([r["total_tokens"] for r in g]) if g else None
            )
            summary[key][mode]["dimension_means"] = {
                dimension: mean(
                    [r["dimensions"][dimension] for r in g if r["dimensions"]]
                )
                for dimension in [
                    "correctness",
                    "completeness",
                    "relevance",
                    "clarity",
                    "reasoning",
                ]
            }
            summary[key][mode]["repeat_means"] = [
                {
                    "repeat": rep,
                    "tokens": mean(
                        [r["total_tokens"] for r in g if r["repeat"] == rep]
                    ),
                    "score": mean(
                        [
                            r["score"]
                            for r in g
                            if r["repeat"] == rep and r["score"] is not None
                        ]
                    ),
                }
                for rep in range(3)
            ]
    rng = random.Random(5660)
    for treatment, control in [("pruner", "baseline")] + ([("recovery", "pruner")] if "recovery" in MODES else []):
        for metric in ["total_tokens", "score"]:
            pairs = []
            for index in protocol["question_indices"]:
                groups = [
                    [r for r in rows if r["index"] == index and r["mode"] == m]
                    for m in [treatment, control]
                ]
                if all(
                    len(g) == 3 and all(r[metric] is not None for r in g)
                    for g in groups
                ):
                    pairs.append(
                        {
                            "index": index,
                            "difference": mean([r[metric] for r in groups[0]])
                            - mean([r[metric] for r in groups[1]]),
                        }
                    )
            diffs = [p["difference"] for p in pairs]
            samples = (
                sorted(mean(rng.choices(diffs, k=len(diffs))) for _ in range(10000))
                if diffs
                else []
            )
            summary["paired"][f"{treatment}-{control}:{metric}"] = {
                "pairs": pairs,
                "mean_difference": mean(diffs),
                "ci95": [samples[249], samples[9749]] if samples else None,
            }
    # Replicate the authors' pairwise intersection and any-dimension-equals-one exclusion.
    summary["author_filtered_pairs"] = {}
    for treatment, control in [("pruner", "baseline")] + ([("recovery", "pruner")] if "recovery" in MODES else []):
        eligible = []
        for r in rows:
            if r["mode"] != treatment:
                continue
            other = next(
                (
                    x
                    for x in rows
                    if x["mode"] == control
                    and x["index"] == r["index"]
                    and x["repeat"] == r["repeat"]
                ),
                None,
            )
            if (
                other
                and r["author_filtered_eligible"]
                and other["author_filtered_eligible"]
            ):
                eligible.append((r["score"], other["score"]))
        summary["author_filtered_pairs"][treatment + "-" + control] = {
            "n": len(eligible),
            "treatment_score": mean([x[0] for x in eligible]),
            "control_score": mean([x[1] for x in eligible]),
        }
    summary["question_means"] = []
    for index in protocol["question_indices"]:
        for mode in MODES:
            group = [r for r in rows if r["index"] == index and r["mode"] == mode]
            summary["question_means"].append(
                {
                    "index": index,
                    "mode": mode,
                    "n": len(group),
                    **{
                        metric: mean(
                            [r[metric] for r in group if r[metric] is not None]
                        )
                        for metric in [
                            "score",
                            "total_tokens",
                            "api_requests",
                            "author_rounds",
                        ]
                    },
                    "prune_calls": sum(r["prune_calls"] for r in group),
                    "expand_calls": sum(r["expand_calls"] for r in group),
                }
            )
    # Post-hoc influence diagnostics retain the primary all-question population.
    summary["leave_one_question_out"] = {}
    for comparison, paired in summary["paired"].items():
        summary["leave_one_question_out"][comparison] = [
            {
                "omitted_index": item["index"],
                "mean_difference": mean(
                    [
                        other["difference"]
                        for other in paired["pairs"]
                        if other["index"] != item["index"]
                    ]
                ),
            }
            for item in paired["pairs"]
        ]
    for name, obj in [("cells", rows), ("attempts", attempts), ("analysis", summary)]:
        (OUT / (name + ".json")).write_text(json.dumps(obj, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "pending": len(pending),
                "cells": len(rows),
                "conditions": summary["conditions"],
            },
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
