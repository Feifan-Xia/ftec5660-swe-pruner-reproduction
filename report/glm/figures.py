"""Make publication figures directly from the complete paired experiment table."""

import json
import statistics
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
MODES = ["baseline", "pruner", "recovery"]
LABELS = ["Full observations", "SWE-Pruner", "+ Exact recovery"]
COLORS = ["#426B9E", "#299A83", "#CC8A35"]


def main():
    analysis = json.loads((ROOT / "results/glm/analysis.json").read_text())
    rows = json.loads((ROOT / "results/glm/cells.json").read_text())
    assert analysis["final"] and not analysis["pending"] and len(rows) == 72
    questions = json.loads((ROOT / "revision_glm/protocol.json").read_text())[
        "question_indices"
    ]
    fig, axes = plt.subplots(1, 2, figsize=(7, 3.15), layout="constrained")
    for ax, metric, scale in zip(axes, ["total_tokens", "score"], [1000, 1]):
        for number, (mode, label, color) in enumerate(zip(MODES, LABELS, COLORS)):
            groups = [
                [
                    r[metric] / scale
                    for r in rows
                    if r["mode"] == mode and r["index"] == index
                ]
                for index in questions
            ]
            means = [statistics.mean(group) for group in groups]
            deviations = [statistics.stdev(group) for group in groups]
            locations = np.arange(len(questions)) + (number - 1) * 0.24
            ax.errorbar(
                locations,
                means,
                yerr=deviations,
                fmt="o",
                markersize=3.6,
                capsize=2,
                linewidth=0.9,
                color=color,
                label=label,
            )
        ax.set_xticks(range(len(questions)), questions)
        ax.set_xlabel("Question index (zero-based)", fontsize=8)
        ax.tick_params(labelsize=8)
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color="#DDE4EA", linewidth=0.5)
    axes[0].set_ylabel("Cumulative API tokens (K)", fontsize=8)
    axes[1].set_ylabel("GPT-5 rubric mean / 10", fontsize=8)
    axes[1].set_ylim(0, 10.5)
    axes[0].legend(fontsize=7, frameon=False, loc="upper left")
    fig.savefig(OUT / "question_results.png", dpi=220)
    fig.savefig(OUT / "question_results.pdf")
    plt.close(fig)

    fig, axes = plt.subplots(1, 2, figsize=(7, 2.65), layout="constrained")
    stats = analysis["conditions"]
    cached = [stats[m]["mean_cached_tokens"] / 1000 for m in MODES]
    uncached = [
        (stats[m]["mean_input_tokens"] - stats[m]["mean_cached_tokens"]) / 1000
        for m in MODES
    ]
    output = [stats[m]["mean_output_tokens"] / 1000 for m in MODES]
    axes[0].bar(range(3), cached, label="Cached input", color="#9CB9D3")
    axes[0].bar(
        range(3), uncached, bottom=cached, label="Uncached input", color="#426B9E"
    )
    axes[0].bar(
        range(3),
        output,
        bottom=np.array(cached) + np.array(uncached),
        label="Output",
        color="#CC8A35",
    )
    axes[0].set_ylabel("Mean API tokens (K)", fontsize=8)
    axes[0].legend(fontsize=7, frameon=False)
    axes[1].bar(
        range(3), [stats[m]["sum_cost"] / stats[m]["n"] for m in MODES], color=COLORS
    )
    axes[1].set_ylabel("Agent cost per selected run (USD)", fontsize=8)
    for ax in axes:
        ax.set_xticks(range(3), ["Full", "Pruner", "Recovery"])
        ax.tick_params(labelsize=8)
        ax.spines[["top", "right"]].set_visible(False)
    fig.savefig(OUT / "resource_breakdown.png", dpi=220)
    fig.savefig(OUT / "resource_breakdown.pdf")
    plt.close(fig)


if __name__ == "__main__":
    main()
