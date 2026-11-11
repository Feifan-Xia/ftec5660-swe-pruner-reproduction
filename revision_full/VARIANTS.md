# 固定子集的代码对照

每个在线阶段保存独立启动快照，以便核对历史执行。`runtime/main.py` 的大部分代码来自作者；评审可先看下表中的实际改动和隔离检查。

| 阶段 | Agent 工具契约 | 输出处理 | 核心比较 |
| --- | --- | --- | --- |
| precision / baseline | 作者完整输出工具 | 原始捕获文本 | 原协议 full 对照，8 题 × 3 次 |
| precision / pruner | 作者 optional hint | 非空 hint 触发原 skimmer | 原协议复现，8 题 × 3 次 |
| hintfull | required nonempty hint | 返回全部原始捕获文本 | 相同 action schema 的机制对照，8 题首轮 |
| hint | required nonempty hint | 原 skimmer | 剪枝触发策略诊断，8 题首轮 |
| recovery | 与 hint 相同 | 原 skimmer＋任务级保存＋expand | 有界原始观测恢复，8 题首轮 |

`revision_hintfull/runtime/main.py`、`revision_hint/runtime/main.py` 和 `revision_recovery/runtime/main.py` 字节相同。Hintfull 只替换 `PrunerBashExecutor.__call__`，其余 AST 与 hint 相同。Recovery 的 `tool_utils.py` 与 hint 字节相同；main 中已有的 recovery 分支挂接 `recovery_tool.py`。这将原协议、触发适配与恢复扩展分别测量。

原始 optional-hint 实验是复现主对照。Required-hint 是明确标记的策略适配；matched-full 让这一工具契约下的文本过滤效应有独立参照。Recovery 与 required-hint 比较时保持相同契约。三个单次诊断组按时间先后运行；完整报告需讨论调查路径和时间顺序对精度的限制。

运行前的输入、模型、源代码、阈值和问卷集合由各阶段 `protocol.json` 及 `runs/<stage>/formal/runtime_manifest.json` 固定。运行故障由独立 recovery wrapper 处理，所有 attempt 目录和评分请求保留。低分答案按原样进入统计。

隔离检查：`revision_hint/test_policy.py`、`revision_hintfull/test_control.py`、`revision_recovery/test_binding.py`。数值重放、schema 对比和原始问卷匹配记录位于 `results/full/`。
