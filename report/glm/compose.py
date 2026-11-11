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
    percentages = read(ROOT / "results/glm/percentage_effects.json")
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
    score_delta = 100 * (c["pruner"]["mean_score"] / c["baseline"]["mean_score"] - 1)
    recovery_delta = 100 * (c["recovery"]["mean_score"] / c["pruner"]["mean_score"] - 1)
    for language in ["zh", "en"]:
        zh = language == "zh"
        labels = (
            ["完整观测", "SWE-Pruner", "剪枝＋精确恢复"]
            if zh
            else ["Full observations", "SWE-Pruner", "+ Exact recovery"]
        )
        fields = dict(notes[language])
        reference = read(ROOT / "configs/paper_reference.json")
        published = {r["condition"]: r for r in reference["rows"] if r["model"] == "GLM-4.6"}
        paper_base = published["baseline"]
        main_rows = []
        for mode, label in zip(["baseline", "pruner"], labels[:2]):
            stat = published[mode]
            main_rows.append([
                ("原文 · " if zh else "Paper · ") + label,
                f"{stat['average_score']:.2f}",
                f"{stat['average_tokens']/1000:.1f}",
                f"{stat['average_rounds']:.1f}",
                f"{(stat['average_tokens']/paper_base['average_tokens']-1)*100:+.1f}%",
                f"{100*(stat['average_score']/paper_base['average_score']-1):+.1f}%",
            ])
        for mode, label in zip(MODES, labels):
            stat = c[mode]
            score_sd = statistics.stdev(x["score"] for x in stat["repeat_means"])
            token_sd = statistics.stdev(x["tokens"] for x in stat["repeat_means"]) / 1000
            main_rows.append([
                ("本次 · " if zh else "Ours · ") + label,
                f"{stat['mean_score']:.2f} ± {score_sd:.2f}",
                f"{stat['mean_total_tokens']/1000:.1f} ± {token_sd:.1f}",
                f"{stat['mean_author_rounds']:.1f}",
                f"{(stat['mean_total_tokens']/c['baseline']['mean_total_tokens']-1)*100:+.1f}%",
                f"{100*(stat['mean_score']/c['baseline']['mean_score']-1):+.1f}%",
            ])
        headers = (["来源与条件", "评分 / 10", "累计 tokens K", "平均轮数", "token 变化", "评分变化"] if zh
                   else ["Source / condition", "Score / 10", "Total tokens K", "Mean rounds", "Token change", "Score change"])
        fields["MAIN_RESULTS"] = (
            "表 3. 原论文与本次复现的 GLM-4.6 结果。变化列相对于各自研究的完整观测组；本次均值 ± SD 来自三次八题整组均值。"
            if zh else "Table 3. Published and reproduced GLM-4.6 results. Changes use each study's own full-observation baseline. Local mean ± SD summarizes three eight-question repetition means."
        ) + "\n\n" + table(headers, main_rows)
        fields["MAIN_RESULTS"] += "\n\n" + (
            "原文为表 2 的 Streamlink 汇总；本次为预选八题×三次，每组 24/24 均完成并评分。两者采用不同题目范围；原文未提供表内 SD。轮数按作者 stats.py 统计 agent/user 来源事件。本次完整／剪枝／恢复的平均 API 请求数为 10.75／9.83／11.58。"
            if zh else "Published rows are the Streamlink aggregates in Table 2; local rows cover eight selected questions × three executions, all 24/24 answered and scored per condition. Populations differ; published SD is unavailable. Rounds follow author stats.py agent/user events. Local full/pruner/recovery API calls average 10.75/9.83/11.58."
        )
        paired_rows = []
        for treatment, control, label in [
            ("pruner", "baseline", "剪枝－完整" if zh else "Pruner − full"),
            ("recovery", "pruner", "恢复－剪枝" if zh else "Recovery − pruner"),
        ]:
            token = percentages["paired"][f"{treatment}-{control}:total_tokens"]
            score = percentages["paired"][f"{treatment}-{control}:score"]
            paired_rows.append(
                [
                    label,
                    f"{token['relative_change_percent']:+.1f}% [{token['ci95_percent'][0]:.1f}, {token['ci95_percent'][1]:.1f}]",
                    f"{score['relative_change_percent']:+.1f}% [{score['ci95_percent'][0]:.1f}, {score['ci95_percent'][1]:.1f}]",
                ]
            )
        fields["UNCERTAINTY"] = ("表 4. 本次复现内部的配对差异与 95% 置信区间。" if zh else "Table 4. Paired differences and 95% confidence intervals within the reproduction.") + "\n\n" + table(
            (
                ["配对比较", "token 相对变化 [95% 区间]", "评分相对变化 [95% 区间]"]
                if zh
                else [
                    "Paired comparison",
                    "Token change % [95% CI]",
                    "Score change % [95% CI]",
                ]
            ),
            paired_rows,
        )
        fields["UNCERTAINTY"] += "\n\n" + (
            "变化率为（处理组均值／对照组均值−1）×100%。以八题为 cluster，保留题内三次执行，种子 5660 重采样 10,000 次并重算两组均值；区间同为百分比。图中 SD 描述题内执行波动。"
            if zh
            else "Change = 100 × (treatment mean / control mean − 1). Intervals, also in percent, resample eight question clusters 10,000 times with seed 5660, recomputing both means and retaining all three executions per question. Figure error bars show within-question SD."
        )
        filtered = analysis["author_filtered_pairs"]["pruner-baseline"]
        fields["PAPER_COMPARISON"] = (
            f"剪枝相对完整观测的 tokens 在论文中降低 54.4%，本次{change(reduction, True)}；评分相对变化分别为 0.0% 与 {score_delta:+.1f}%。作者评分过滤规则保留本次全部 {filtered['n']} 对题次，过滤口径下的本次评分与表 3 一致。固定路由、样本构成和评分部署的差异见第 3、5 节。"
            if zh else f"Pruning reduces published tokens by 54.4%; locally they {change(reduction, False)}. Relative score changes are 0.0% and {score_delta:+.1f}%. Author score filtering retains all {filtered['n']} local pairs, leaving Table 3 scores unchanged. Sections 3 and 5 describe population, route and judge differences."
        )
        r = c["recovery"]
        fields["AUTONOMOUS_RECOVERY"] = (
            f"恢复组在 {r['expansion_tasks']}/24 个任务中成功展开，记录 {r['sum_expand_tool_actions']} 次展开动作和 {r['sum_expand_calls']} 次成功读取，返回 {r['sum_expanded_chars']:,} 个字符，其中重复行 {r['sum_repeated_lines']} 行。对照上一次展示内容，{recovery['reads_exposing_new_lines']}/{recovery['successful_reads']} 次读取暴露了此前未展示的非空行。相对剪枝组，评分变化 {recovery_delta:+.1f}%、累计 tokens {change(recovery_reduction, True)}。是否展开还受任务难度和 Agent 自选行为影响；下面通过固定上下文干预检查取回证据这一机制。"
            if zh
            else f"Recovery succeeds in {r['expansion_tasks']}/24 tasks, with {r['sum_expand_tool_actions']} expansion actions and {r['sum_expand_calls']} successful reads, returning {r['sum_expanded_chars']:,} characters and {r['sum_repeated_lines']} repeated lines. Compared with the preceding display, {recovery['reads_exposing_new_lines']}/{recovery['successful_reads']} reads expose previously absent nonblank lines. Relative to pruning, score changes by {recovery_delta:+.1f}% and tokens {change(recovery_reduction, False)}. Task difficulty and self-selected tool use also affect uptake; the following intervention isolates access to saved evidence."
        )
        fields["MECHANISM_TABLE"] = (
            "表 5. 固定目标变化实验的准确性与资源消耗，三组各 24 次。"
            if zh else "Table 5. Accuracy and resource use under the fixed goal-shift intervention, 24 runs per condition."
        ) + "\n\n" + table(
            (["条件", "SR%（成功数）", "输入 tokens", "输出 tokens", "累计 tokens", "费用 USD"] if zh
             else ["Condition", "SR% (count)", "Input tokens", "Output tokens", "Total tokens", "Cost USD"]),
            [[label, f"{100*mechanism['conditions'][mode]['correct']/24:.1f}% ({mechanism['conditions'][mode]['correct']}/24)",
              f"{mechanism['conditions'][mode]['input_tokens']:,}",
              f"{mechanism['conditions'][mode]['output_tokens']:,}",
              f"{mechanism['conditions'][mode]['input_tokens']+mechanism['conditions'][mode]['output_tokens']:,}",
              f"{mechanism['conditions'][mode]['cost']:.6f}"]
             for mode,label in zip(["full","pruned","recoverable"],
                ["完整观测","剪后观测","精确恢复"] if zh else ["Full","Pruned","Recoverable"])],
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
            f"主实验首轮三组分别导出 {counts} 个完整答案，共保存 {analysis['attempts']} 条正式尝试；最终所有 72 个计划项均完成评分。固定路由主实验与机制实验已报告 API 费用合计 ${checks['known_provider_cost_usd']:.4f}；包含旧阶段、开发记录和保守占用的项目账本为 ${checks['project_conservative_usd']:.4f}。原始记录、启动快照和逐项审计均随材料保存。"
            if zh
            else f"First attempts export {counts} complete answers in full/pruner/recovery order; {analysis['attempts']} formal attempts are retained and all 72 planned cells are scored. Fixed-route main/mechanism calls report ${checks['known_provider_cost_usd']:.4f}. Project accounting, including earlier stages, development and conservative reservations, totals ${checks['project_conservative_usd']:.4f}. Raw evidence, launch snapshots and cell-level audit accompany the report."
        )
        source = (OUT / f"template_{language}.md").read_text(encoding="utf-8")
        for key, value in fields.items():
            source = source.replace("{{" + key + "}}", value)
        assert "{{" not in source, "Every report section needs reviewed content"
        (OUT / f"report_{language}.md").write_text(source, encoding="utf-8")
    print("Composed both audited report sources.")


if __name__ == "__main__":
    main()
