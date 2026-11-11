"""Summarize all predeclared goal-shift cases, including preserved targets."""

import argparse, json, statistics, random
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "runs/recovery/mechanism"
OUT = ROOT / "results/recovery"
OUT.mkdir(parents=True, exist_ok=True)


def read(p):
    return json.loads(p.read_text(encoding="utf-8"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--partial", action="store_true")
    args = parser.parse_args()
    rows = []
    pending = []
    cases = [read(BASE / f"case{i}.json") for i in range(8)]
    for i in range(8):
        for mode in ["full", "pruned", "recoverable"]:
            for repeat in range(3):
                path = BASE / mode / f"case{i}_r{repeat}.json"
                if not path.exists():
                    pending.append([i, mode, repeat])
                    continue
                d = read(path)
                usage = [p.get("usage", {}) for p in d["responses"]]
                rows.append(
                    {
                        k: d[k]
                        for k in [
                            "case",
                            "mode",
                            "repeat",
                            "correct",
                            "target_value_retained",
                        ]
                    }
                    | {
                        "expands": len(d["reads"]),
                        "returned_chars": sum(r["returned_chars"] for r in d["reads"]),
                        "input_tokens": sum(u.get("prompt_tokens", 0) for u in usage),
                        "output_tokens": sum(
                            u.get("completion_tokens", 0) for u in usage
                        ),
                        "cost": sum(u.get("cost", 0) for u in usage),
                    }
                )
    if not args.partial:
        assert len(rows) == 72 and not pending, "Complete all predeclared cases"
    result = {
        "final": not args.partial,
        "pending": pending,
        "n": len(rows),
        "conditions": {},
        "cases": [],
        "rows": rows,
    }
    for mode in ["full", "pruned", "recoverable"]:
        g = [r for r in rows if r["mode"] == mode]
        result["conditions"][mode] = {
            "n": len(g),
            "correct": sum(r["correct"] for r in g),
            "expands": sum(r["expands"] for r in g),
            "returned_chars": sum(r["returned_chars"] for r in g),
            "input_tokens": sum(r["input_tokens"] for r in g),
            "output_tokens": sum(r["output_tokens"] for r in g),
            "cost": sum(r["cost"] for r in g),
        }
    for i, case in enumerate(cases):
        result["cases"].append(
            {
                "case": i,
                "path": case["path"],
                "constant": case["constant"],
                "target_value_retained": case["target_value_retained"],
                "source_tokens": case["prune"]["origin_token_cnt"],
                "retained_tokens": case["prune"]["left_token_cnt"],
                "conditions": {
                    mode: {
                        "n": len(
                            [r for r in rows if r["case"] == i and r["mode"] == mode]
                        ),
                        "correct": sum(
                            r["correct"]
                            for r in rows
                            if r["case"] == i and r["mode"] == mode
                        ),
                        "expands": sum(
                            r["expands"]
                            for r in rows
                            if r["case"] == i and r["mode"] == mode
                        ),
                    }
                    for mode in ["full", "pruned", "recoverable"]
                },
            }
        )
    (OUT / "mechanism.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps({"n": len(rows), "conditions": result["conditions"]}, indent=2))


if __name__ == "__main__":
    main()
