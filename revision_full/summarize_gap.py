"""Build a Chinese evidence ledger from verified gap diagnostics."""
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def read(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


replay = read("results/full/author_all_observations_replay.json")["summary"]
authorization = read("runs/full/budget_authorization.json")
ledger = [json.loads(s) for s in (ROOT / "runs/full/formal_usage.jsonl").read_text(encoding="utf-8").splitlines()]
spent = authorization["prior_stage_conservative_usd"] + sum(r["cost"] for r in ledger)
text = f'''# SWE-Pruner 固定子集差距诊断

## 当前结论与目标

固定八题的自主运行节省 17.6% tokens，作者相同八题的公开运行记录节省 49.9%。本轮将差距定位到三个可检查层面：剪枝器数值一致性、Agent 的 hint 使用与重读策略、full 基线的搜索成本。完整 48 题扩展暂缓，批准预算保持 USD 12。

小范围确认的工作目标设为：固定八题各三次，平均端到端 tokens 至少减少 40%，平均质量相对下降至多 2%，同时呈现逐题结果、三轮结果和问题簇区间。40% 对应距离作者同题降幅约 10 个百分点。该目标用于判断继续扩展的价值；现有自主运行结果仍为 17.6%。

## 剪枝器固定输入一致性

本轮使用作者保存的同一八题全部 131 条剪枝观测，逐条输入原始文本、原始 hint 和阈值 0.5，保留短输出、未改变输出及超时文本。固定原始输入后，直接检验本地实现能否复现作者剪枝文本。

| 指标 | 作者记录 | 本地重放 |
|---|---:|---:|
| 观测数 | 131 | 131 |
| 原始 tokens | {replay['author_raw']:,} | {replay['local_raw']:,} |
| 保留 tokens | {replay['author_kept']:,} | {replay['local_kept']:,} |
| 文本压缩率 | {replay['author_compression_percent']:.4f}% | {replay['local_compression_percent']:.4f}% |
| 与作者逐字一致 | 参考 | {100 * replay['exact_text_count'] / replay['n']:.2f}%（127/131） |
| 本地服务失败 | — | 0 |

两者压缩率相差 {replay['local_compression_percent'] - replay['author_compression_percent']:.4f} 个百分点，净保留量相差 27 tokens。四条残余差异位于 q14、q30 和 q11，逐行 diff 已保存。该结果支持当前 skimmer 在已知作者输入上的高度一致性；自主运行仍取决于 Agent 实际产生的命令、hint 和重读。

证据：results/full/author_all_observations_replay.json、author_replay_residual_diffs.json；131 条原始重放输出位于 runs/full/diagnostics/author_all_replay/。全部重放使用本地 GPU，付费 API 调用数为零。

## 工具调用与搜索路径

| 指标 | 作者 full | 作者 pruner | 本地 full | 本地 pruner |
|---|---:|---:|---:|---:|
| 执行项 | 8 | 8 | 24 | 24 |
| 每题 Bash 次数 | 18.00 | 16.38 | 11.54 | 10.58 |
| Bash hint 使用率 | — | 100.00% | — | 2.36% |
| 命令超时数 | 9 | 1 | 0 | 0 |
| 发生超时的任务比例 | 50.0% | 12.5% | 0.0% | 0.0% |
| 平均累计 API tokens K | 190.2 | 95.3 | 136.4 | 112.3 |
| 平均质量 / 10 | 8.25 | 8.60 | 9.00 | 9.12 |

作者 pruner 的 131 次 Bash 全部带 hint；本地只有 6/254 次。以任务为分母时，分别为 100% 与 25%。源码、工具 schema 和提示词对齐后，这一行为差异依然存在。

本地总 tokens 的 −17.62% 可以精确分解为请求数 −17.70% 与每请求平均 tokens +0.10% 的乘积变化。当前总体收益主要体现为请求更少；原有数据对剪枝造成累计上下文下降的支持较弱。

作者 q41 的 full 在前期搜索中遇到四次超时，随后反复在 Conan 中寻找 Streamlink 的 TestIO，执行到 50 步上限，评分 2.8。其 tokens 为 146.2K，本地三次均值为 32.3K、评分 8.67。q8 作者 full 也有三次超时和跨仓库探索，193.8K 对应本地 43.3K。轨迹说明作者基线包含额外失败与搜索成本；环境、模型路径和运行时机共同变化，现有记录支持过程解释。

同题绝对节省差为每题 70.9K tokens，其中本地 full 低 53.8K，占差额约 76%；本地 pruner 高 17.0K，占约 24%。该拆分是算术归因。原始网关内部提示、模型权重版本与推理设置仍缺少可核查记录。

证据：results/full/trajectory_gap_audit.json 包含每题轨迹成员、命令和超时事件；author_same_questions.json 包含问题哈希及作者与本地记录定位。

## 策略兼容探针与判定

原公开契约把 hint 设为可选。已有“每次强制非空”诊断使过滤覆盖达到 100%，同时相对匹配 full 增加 32.5% tokens。其失败模式包含同一文件被重复读取、局部细节持续被过滤。这个结果要求保留明确的完整读取路径。

本轮在原有三道开发题 43、26、17 上完成两组探针，开发题与固定八题分开：

| 探针 | 对照结果 | 处理结果 | 判断 |
|---|---|---|---|
| 字段必填但允许空值，读取文件前的三次续接 | optional：1/3 带 hint | required：1/3 带 hint | 未改善长文件读取触发 |
| 同一首条命令及相同输出，只改变历史 action 的 hint 字段 | 无 hint 历史：0/3 后续带 hint | 有 hint 历史：2/3 后续带 hint | 支持测试首次引导 |

第一组共 12 次请求，第二组共 6 次请求。所有结果均保留。第一组未达到预先写定的启动条件，因此停止该候选。第二组达到启动条件，后续六项开发实验只在首个 API 请求要求非空 hint，随后恢复原始可选 schema；匹配 full 使用相同接口与引导，仅执行器返回完整文本。这一候选属于明确标记的服务策略适配。

开发实验的预设条件为：三道题中至少两道在首请求以后继续触发剪枝，聚合 tokens 下降，平均质量相对下降至多 2%。满足条件后，再为固定八题的三重复确认冻结独立协议。保留全部题目、首次有效答案和失败记录。

'''
pilot = ROOT / "results/full/priming_development.json"
if pilot.exists():
    p = read("results/full/priming_development.json")
    g = p["groups"]; d = p["changes_percent"]
    text += f'''开发实验六项完成。完整输出与剪枝的平均 tokens 为 {g['baseline']['total_tokens']:.0f}/{g['pruner']['total_tokens']:.0f}（{d['total_tokens']:+.1f}%），平均质量 {g['baseline']['score']:.2f}/{g['pruner']['score']:.2f}（{d['score']:+.1f}%）。剪枝组 {g['pruner']['later_hint_tasks']}/3 项在首次调用以后继续使用 hint。启动条件判定：{'通过' if p['go_gate_passed'] else '未通过'}。逐请求审计确认首次 schema 改变、后续恢复可选字段。

q43、q26、q17 的 full/pruner 质量分别为 10/10、9.2/7.0、8.0/7.4。该候选因质量条件未通过而停止固定八题确认。后验源码审计发现 q17 的参考答案把正常请求阻止写成异常终止，q26 把两种响应上的 regex 描述成同一 JavaScript 上的多次扫描；两组生成答案也存在未经验证的复杂度推断。原始官方评分与门槛判定完整保留，详细源码证据见 results/full/development_reference_audit.json。当前 37.7% 节省属于三道开发题结果，接近作者降幅且保持质量的固定八题目标仍待达到。

'''
else:
    text += "六项开发实验已冻结并正在执行，结果待完整配对后填写。\n\n"
text += f'''## 预算与下一阶段

本次记录时保守累计 USD {spent:.4f}，批准上限 USD 12。完整 48 题扩展暂缓。先完成机制诊断与固定范围的策略验证，再决定是否需要更接近作者的模型部署或新的预算。独立的原始观测恢复修改继续保留原协议数据，后续改进评价使用确认后的同一基线与同一执行配置。
'''
(ROOT / "revision_full/GAP_FINDINGS.md").write_text(text, encoding="utf-8")
print(f"Wrote gap findings; project conservative USD {spent:.4f}")
