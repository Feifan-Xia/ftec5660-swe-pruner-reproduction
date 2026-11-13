"""Plot the complete fixed-eight three-condition experiment."""
import json
import statistics
from pathlib import Path

import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]
ROWS = json.loads(
    (ROOT / "results/precision/cells.json").read_text(encoding="utf-8")
) + json.loads(
    (ROOT / "results/optional/cells.json").read_text(encoding="utf-8")
)
INDICES = [41, 14, 30, 8, 11, 46, 33, 29]
MODES = ["baseline", "pruner", "recovery"]
LABELS = ["Full", "Pruner", "Pruner + recovery"]
COLORS = ["#5D6877", "#197F75", "#D1793F"]


def mean_for(index, mode, metric):
    values = [
        row[metric]
        for row in ROWS
        if row["index"] == index and row["mode"] == mode
    ]
    return statistics.mean(values)


plt.rcParams.update(
    {
        "font.family": "DejaVu Sans",
        "font.size": 10,
        "axes.spines.top": False,
        "axes.spines.right": False,
    }
)
fig, axes = plt.subplots(1, 2, figsize=(11.2, 4.7), gridspec_kw={"width_ratios": [1.45, 1]})

ax = axes[0]
y = list(range(len(INDICES)))
for mode, label, color, offset in zip(MODES, LABELS, COLORS, [-0.18, 0, 0.18]):
    values = [mean_for(index, mode, "total_tokens") / 1000 for index in INDICES]
    ax.scatter(values, [position + offset for position in y], s=42, color=color, label=label, zorder=3)
    for position, value in zip(y, values):
        ax.plot([value, value], [position + offset, position + offset], color=color, alpha=0.35, linewidth=1)
ax.set_yticks(y, [f"q{index}" for index in INDICES])
ax.set_xscale("log")
ax.set_xlabel("Mean cumulative API tokens per task (K, log scale)")
ax.set_title("(a) All eight fixed questions", loc="left", fontsize=12, fontweight="bold")
ax.grid(axis="x", color="#D8DEE6", linewidth=0.7, alpha=0.7)
ax.legend(frameon=False, loc="lower right")

ax = axes[1]
x = list(range(3))
width = 0.24
for mode_index, (mode, label, color) in enumerate(zip(MODES, LABELS, COLORS)):
    values = [
        statistics.mean(
            row["total_tokens"]
            for row in ROWS
            if row["repeat"] == repeat and row["mode"] == mode
        )
        / 1000
        for repeat in range(3)
    ]
    positions = [position + (mode_index - 1) * width for position in x]
    bars = ax.bar(positions, values, width=width, color=color, label=label)
    for bar, value in zip(bars, values):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            value + 2,
            f"{value:.0f}",
            ha="center",
            va="bottom",
            fontsize=8,
        )
ax.set_xticks(x, ["Repeat 1", "Repeat 2", "Repeat 3"])
ax.set_ylabel("Mean cumulative API tokens (K)")
ax.set_title("(b) Group mean by repetition", loc="left", fontsize=12, fontweight="bold")
ax.grid(axis="y", color="#D8DEE6", linewidth=0.7, alpha=0.7)
ax.set_axisbelow(True)

fig.tight_layout(pad=1.8)
out = ROOT / "report/revised/figures/one_batch.png"
out.parent.mkdir(parents=True, exist_ok=True)
fig.savefig(out, dpi=220, bbox_inches="tight", facecolor="white")
print(out)
