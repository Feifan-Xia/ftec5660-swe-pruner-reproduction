"""Derive relative effects, clustered intervals and diagnostics from saved runs."""

import ast
import json
import random
from pathlib import Path
from statistics import mean

ROOT = Path(__file__).resolve().parents[1]


def main():
    rows = json.loads((ROOT / "results/glm/cells.json").read_text(encoding="utf-8"))
    ids = sorted({r["index"] for r in rows})
    modes = ["baseline", "pruner", "recovery"]
    metrics = ["total_tokens", "score"]
    per_question = {
        (i, mode, metric): mean(r[metric] for r in rows if r["index"] == i and r["mode"] == mode)
        for i in ids for mode in modes for metric in metrics
    }

    def effect(selected, treatment, control, metric):
        a = mean(per_question[i, treatment, metric] for i in selected)
        b = mean(per_question[i, control, metric] for i in selected)
        return (a / b - 1) * 100

    result = {"definition": "100 * (treatment mean / control mean - 1); each bootstrap resamples question clusters and recomputes both means", "seed": 5660, "resamples": 10000, "paired": {}, "leave_one_question_out": {}}
    rng = random.Random(5660)
    draws = [rng.choices(ids, k=len(ids)) for _ in range(10000)]
    for treatment, control in [("pruner", "baseline"), ("recovery", "pruner")]:
        for metric in metrics:
            values = sorted(effect(sample, treatment, control, metric) for sample in draws)
            result["paired"][f"{treatment}-{control}:{metric}"] = {
                "relative_change_percent": effect(ids, treatment, control, metric),
                "ci95_percent": [values[249], values[9749]],
            }
    for excluded in ids:
        selected = [i for i in ids if i != excluded]
        result["leave_one_question_out"][str(excluded)] = {
            metric: effect(selected, "pruner", "baseline", metric) for metric in metrics
        }
    mechanisms = json.loads((ROOT / "results/glm/mechanism.json").read_text(encoding="utf-8"))["conditions"]
    result["mechanism_sr_percent"] = {mode: 100 * x["correct"] / x["n"] for mode, x in mechanisms.items()}
    p, r = mechanisms["pruned"], mechanisms["recoverable"]
    result["mechanism_token_increase_percent"] = 100 * ((r["input_tokens"] + r["output_tokens"]) / (p["input_tokens"] + p["output_tokens"]) - 1)
    result["mechanism_fee_increase_percent"] = 100 * (r["cost"] / p["cost"] - 1)
    trees = []
    for relative in ["upstream/downstream_eval/multi_turn/sweqa/openhands-qa/tool_utils.py", "revision_glm/runtime/tool_utils.py"]:
        tree = ast.parse((ROOT / relative).read_text(encoding="utf-8"))
        trees.append({n.name: ast.dump(n, include_attributes=False) for n in tree.body if isinstance(n, (ast.ClassDef, ast.FunctionDef))})
    names = ["PrunerBashAction", "PrunerBashExecutor", "BashObservation", "OriginBashExecutor", "PrunerBashTool", "OriginBashTool"]
    result["author_runtime_contract_ast_equal"] = {name: trees[0][name] == trees[1][name] for name in names}
    assert all(result["author_runtime_contract_ast_equal"].values())
    (ROOT / "results/glm/percentage_effects.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result["paired"], indent=2))


if __name__ == "__main__":
    main()
