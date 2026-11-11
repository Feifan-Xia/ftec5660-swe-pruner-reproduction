# 固定子集的代码对照

每个在线阶段保存独立启动快照，以便核对历史执行。`runtime/main.py` 的大部分代码来自作者；评审可先看下表中的实际改动和隔离检查。

| 阶段 | Agent 工具契约 | 输出处理 | 核心比较 |
| --- | --- | --- | --- |
| precision / baseline | 作者完整输出工具 | 原始捕获文本 | 原协议 full 对照，8 题 × 3 次 |
| precision / pruner | 作者 optional hint | 非空 hint 触发原 skimmer | 原协议复现，8 题 × 3 次 |
| hintfull | required nonempty hint | 返回全部原始捕获文本 | 相同 action schema 的机制对照，8 题首轮 |
| hint | required nonempty hint | 原 skimmer | 剪枝触发策略诊断，8 题首轮 |
| recovery | 与 hint 相同 | 原 skimmer＋任务级保存＋expand | 有界原始观测恢复，8 题首轮 |
| optional / recovery | 作者 optional hint | 原 skimmer＋任务级保存＋expand | 原协议修改主比较，8 题 × 3 次 |
| population（准备中） | 作者 optional hint / full | 同一修复后的主循环，三组 | 余下 40 题 × 3 次；等待预算授权 |

`revision_hintfull/runtime/main.py`、`revision_hint/runtime/main.py` 和 `revision_recovery/runtime/main.py` 字节相同。Hintfull 只替换 `PrunerBashExecutor.__call__`，其余 AST 与 hint 相同。Recovery 的 `tool_utils.py` 与 hint 字节相同；main 中已有的 recovery 分支挂接 `recovery_tool.py`。这将原协议、触发适配与恢复扩展分别测量。

原始 optional-hint 实验是复现主对照。Required-hint 是明确标记的策略适配；matched-full 让这一工具契约下的文本过滤效应有独立参照。Recovery 与 required-hint 比较时保持相同契约。三个单次诊断组按时间先后运行；完整报告需讨论调查路径和时间顺序对精度的限制。

运行前的输入、模型、源代码、阈值和问卷集合由各阶段 `protocol.json` 及 `runs/<stage>/formal/runtime_manifest.json` 固定。运行故障由独立 recovery wrapper 处理，所有 attempt 目录和评分请求保留。低分答案按原样进入统计。

隔离检查：`revision_hint/test_policy.py`、`revision_hintfull/test_control.py`、`revision_recovery/test_binding.py`。数值重放、schema 对比和原始问卷匹配记录位于 `results/full/`。

`revision_optional/runtime/tool_utils.py` 与原始 `revision_subset/runtime/tool_utils.py` 字节相同。其 main 仅通过 `fix_terminal_history.py` 修复终止分支的可见观测序列化，再使用已有 recovery 绑定。24 项 optional recovery 均未触发终止摘要，因此与原始 pruner 的主比较具有相同的实际终止路径契约。绑定测试和 17 文件启动快照已验证。

两个历史受影响任务的终止修复保留相同完整前缀，只重放最后一次摘要及其评分；原始与修复指标分别保存。`results/full/manuscript_evidence.json` 标明各比较的控制组、处理组和区间，`results/full/author_same_questions.json` 标明作者参考运行与本地重复的来源。
