"""Insert audited measurements and reviewed interpretation into both report sources."""

import json
import statistics
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
MODES = ["baseline", "pruner", "recovery"]


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def table(headers, rows):
    return "\n".join(
        [
            "| " + " | ".join(headers) + " |",
            "| " + " | ".join(["---"] * len(headers)) + " |",
        ]
        + ["| " + " | ".join(str(x) for x in row) + " |" for row in rows]
    )


def change(value, zh):
    return (
        (("降低" if value >= 0 else "增加") + f"{abs(value):.1%}")
        if zh
        else (("decreased" if value >= 0 else "increased") + f" by {abs(value):.1%}")
    )


def main():
    analysis = read(ROOT / "results/glm/analysis.json")
    cells = read(ROOT / "results/glm/cells.json")
    mechanism = read(ROOT / "results/glm/mechanism.json")
    recovery = read(ROOT / "results/glm/recovery_trace_analysis.json")
    audit = read(ROOT / "results/glm/audit.json")
    numerics = read(ROOT / "runs/glm/attention_validation.json")
    notes = read(OUT / "reviewed_interpretation.json")
    assert analysis["final"] and mechanism["final"] and audit["status"] == "PASS"
    c = analysis["conditions"]
    reduction = (
        1 - c["pruner"]["mean_total_tokens"] / c["baseline"]["mean_total_tokens"]
    )
    recovery_reduction = (
        1 - c["recovery"]["mean_total_tokens"] / c["pruner"]["mean_total_tokens"]
    )
    score_delta = c["pruner"]["mean_score"] - c["baseline"]["mean_score"]
    recovery_delta = c["recovery"]["mean_score"] - c["pruner"]["mean_score"]
    for language in ["zh", "en"]:
        zh = language == "zh"
        labels = (
            ["完整观测", "SWE-Pruner", "剪枝＋精确恢复"]
            if zh
            else ["Full observations", "SWE-Pruner", "+ Exact recovery"]
        )
        fields = dict(notes[language])
        main_rows = []
        for mode, label in zip(MODES, labels):
            stat = c[mode]
            score_sd = statistics.stdev(x["score"] for x in stat["repeat_means"])
            token_sd = (
                statistics.stdev(x["tokens"] for x in stat["repeat_means"]) / 1000
            )
            main_rows.append(
                [
                    label,
                    f"{stat['answered']}/24",
                    f"{stat['mean_score']:.2f} ± {score_sd:.2f}",
                    f"{stat['mean_total_tokens']/1000:.1f} ± {token_sd:.1f}",
                    f"{stat['mean_author_rounds']:.1f}",
                    f"{stat['mean_api_requests']:.1f}",
                ]
            )
        headers = (
            [
                "条件",
                "完整答案",
                "评分均值 ± SD",
                "tokens K ± SD",
                "作者轮数",
                "API 请求",
            ]
            if zh
            else [
                "Condition",
                "Answers",
                "Score ± SD",
                "Tokens K ± SD",
                "Author rounds",
                "API calls",
            ]
        )
        fields["MAIN_RESULTS"] = (
            "全部 72 个计划项已完成并获得独立评分，每组 24 个。均值使用相同的八题、三次执行；SD 是三次整组均值的样本标准差。作者轮数按其 stats.py 计算所有 agent/user 来源事件，API 请求数另列。\n\n"
            if zh
            else "All 72 planned cells are resolved and independently scored, 24 per condition. Means use the same eight questions and three executions; SD is the sample deviation of the three whole-subset means. Author rounds count agent/user-source events using stats.py; API requests are shown separately.\n\n"
        ) + table(headers, main_rows)
        if zh:
            fields[
                "MAIN_RESULTS"
            ] += f"\n\n相对完整观测，剪枝组累计 tokens {change(reduction, True)}，平均评分变化 {score_delta:+.2f}。加入恢复后，相对剪枝组 tokens {change(recovery_reduction, True)}，评分变化 {recovery_delta:+.2f}。"
        else:
            fields[
                "MAIN_RESULTS"
            ] += f"\n\nRelative to full observations, pruning tokens {change(reduction, False)}, with a {score_delta:+.2f} score change. Relative to pruning, recovery tokens {change(recovery_reduction, False)}, with a {recovery_delta:+.2f} score change."
        paired_rows = []
        for treatment, control, label in [
            ("pruner", "baseline", "剪枝－完整" if zh else "Pruner − full"),
            ("recovery", "pruner", "恢复－剪枝" if zh else "Recovery − pruner"),
        ]:
            token = analysis["paired"][f"{treatment}-{control}:total_tokens"]
            score = analysis["paired"][f"{treatment}-{control}:score"]
            paired_rows.append(
                [
                    label,
                    f"{token['mean_difference']/1000:+.1f} [{token['ci95'][0]/1000:.1f}, {token['ci95'][1]/1000:.1f}]",
                    f"{score['mean_difference']:+.2f} [{score['ci95'][0]:.2f}, {score['ci95'][1]:.2f}]",
                ]
            )
        fields["UNCERTAINTY"] = table(
            (
                ["配对比较", "token 差 K [95% 区间]", "评分差 [95% 区间]"]
                if zh
                else [
                    "Paired comparison",
                    "Token difference K [95% CI]",
                    "Score difference [95% CI]",
                ]
            ),
            paired_rows,
        )
        fields["UNCERTAINTY"] += "\n\n" + (
            "区间以 8 道题为 cluster，保留每题内部三次执行，使用种子 5660 重采样 10,000 次。这一配对统计描述子集中的差异，图中的 SD 描述每题执行波动。"
            if zh
            else "Intervals resample eight question clusters 10,000 times with seed 5660, retaining each question’s three executions together. These paired intervals describe subset differences; figure error bars describe within-question execution variation."
        )
        filtered = analysis["author_filtered_pairs"]["pruner-baseline"]
        fields["PAPER_COMPARISON"] = (
            f"本地剪枝组相对完整观测的 tokens {change(reduction, True)}，论文报告降低 54.4%；本地评分差为 {score_delta:+.2f}，论文为 0.00。作者过滤规则在两组共同且五维均不为 1 的题次上保留 {filtered['n']} 对，过滤后完整／剪枝评分为 {filtered['control_score']:.2f}/{filtered['treatment_score']:.2f}。本地范围、评分部署和运行环境已明确记录，因此数值差异需要结合轨迹解释。"
            if zh
            else f"Locally, pruning tokens {change(reduction, False)}, compared with the paper’s 54.4% decrease; the local score difference is {score_delta:+.2f}, versus 0.00 in the paper. The authors’ pairwise filtering rule retains {filtered['n']} pairs with all dimensions above one; filtered full/pruner scores are {filtered['control_score']:.2f}/{filtered['treatment_score']:.2f}. Population, scoring deployment and environment differences require trajectory-level interpretation."
        )
        r = c["recovery"]
        fields["AUTONOMOUS_RECOVERY"] = (
            f"恢复组在 {r['expansion_tasks']}/24 个任务中成功展开，记录 {r['sum_expand_tool_actions']} 次展开动作和 {r['sum_expand_calls']} 次成功读取，返回 {r['sum_expanded_chars']:,} 个字符，其中重复行 {r['sum_repeated_lines']} 行。对照上一次展示内容，{recovery['reads_exposing_new_lines']}/{recovery['successful_reads']} 次读取暴露了此前未展示的非空行。相对剪枝组，评分变化 {recovery_delta:+.2f}、累计 tokens {change(recovery_reduction, True)}。是否展开还受任务难度和 Agent 自选行为影响；下面通过固定上下文干预检查取回证据这一机制。"
            if zh
            else f"Recovery succeeds in {r['expansion_tasks']}/24 tasks, with {r['sum_expand_tool_actions']} expansion actions and {r['sum_expand_calls']} successful reads, returning {r['sum_expanded_chars']:,} characters and {r['sum_repeated_lines']} repeated lines. Compared with the preceding display, {recovery['reads_exposing_new_lines']}/{recovery['successful_reads']} reads expose previously absent nonblank lines. Relative to pruning, score changes by {recovery_delta:+.2f} and tokens {change(recovery_reduction, False)}. Task difficulty and self-selected tool use also affect uptake; the following intervention isolates access to saved evidence."
        )
        fields["MECHANISM_TABLE"] = table(
            (
                ["文件", "目标值保留", "完整", "剪后", "可恢复"]
                if zh
                else ["File", "Target retained", "Full", "Pruned", "Recoverable"]
            ),
            [
                [
                    Path(case["path"]).name,
                    (
                        ("是" if case["target_value_retained"] else "否")
                        if zh
                        else str(case["target_value_retained"])
                    ),
                    *[
                        f"{case['conditions'][mode]['correct']}/3"
                        for mode in ["full", "pruned", "recoverable"]
                    ],
                ]
                for case in mechanism["cases"]
            ],
        )
        fields["NUMERICAL_TABLE"] = table(
            (
                [
                    "输入 tokens",
                    "参考路径",
                    "参考／分块秒",
                    "参考／分块 GiB",
                    "阈值决策差",
                ]
                if zh
                else [
                    "Input tokens",
                    "Reference",
                    "Ref./tiled seconds",
                    "Ref./tiled GiB",
                    "Decision changes",
                ]
            ),
            [
                [
                    x["input_tokens"],
                    x["reference"],
                    f"{x['baseline_seconds']:.2f}/{x['tiled_seconds']:.2f}",
                    f"{x['baseline_peak_bytes']/2**30:.2f}/{x['tiled_peak_bytes']/2**30:.2f}",
                    x["threshold_0_5_disagreements"],
                ]
                for x in numerics
            ],
        )
        first = analysis["first_attempt"]
        counts = "/".join(str(first[m]["answered"]) for m in MODES)
        checks = audit["checks"]
        fields["COMPLETENESS_AND_COST"] = (
            f"主实验首轮三组分别导出 {counts} 个完整答案，共保存 {analysis['attempts']} 条正式尝试；最终所有 72 个计划项均完成评分。固定路由主实验与机制实验已报告 API 费用合计 ${checks['known_provider_cost_usd']:.4f}；包含旧阶段、开发记录和保守占用的项目账本为 ${checks['project_conservative_usd']:.4f}，用户批准上限为 $12。原始记录、启动快照和逐项审计均随材料保存。"
            if zh
            else f"First attempts export {counts} complete answers in full/pruner/recovery order; {analysis['attempts']} formal attempts are retained and all 72 planned cells are scored. Fixed-route main/mechanism calls report ${checks['known_provider_cost_usd']:.4f}. Project accounting, including earlier stages, development and conservative reservations, totals ${checks['project_conservative_usd']:.4f} against the approved $12 ceiling. Raw evidence, launch snapshots and cell-level audit accompany the report."
        )
        source = (OUT / f"template_{language}.md").read_text(encoding="utf-8")
        for key, value in fields.items():
            source = source.replace("{{" + key + "}}", value)
        assert "{{" not in source, "Every report section needs reviewed content"
        (OUT / f"report_{language}.md").write_text(source, encoding="utf-8")
    print("Composed both audited report sources.")


if __name__ == "__main__":
    main()
