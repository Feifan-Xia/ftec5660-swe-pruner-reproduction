# SWE-Pruner 复现偏差诊断

## 诊断目标

复现对象为 SWE-Pruner 论文表 2 中 Streamlink × GLM-4.6 的 full 与 pruner 两行。作者以 OpenHands 驱动多步仓库探索，用 SWE-QA 的问题、参考答案和五维评分评价答案。原文平均 tokens 从 318.2K 降至 145.1K，质量均为 8.56/10。

上一轮 8 题、每题 3 次的结果为 112.8K → 131.0K（+16.1%），端到端节省目标尚未复现。本次修订首先核对实现与统计，再扩展到发布的全部 48 题。

## 已验证的统计行为

`results/full/prior_audit.json` 逐一核对 72 个任务与 772 次 agent API 请求。所有导出的 token 总量均等于 API 的 input + output 累计量；实际请求使用同一个 system prompt、GLM-4.6/Z.AI、temperature=0、top_p=1、max_tokens=16384。原始响应保留缓存与 reasoning 用量。

公开 runner 分别累加 `accumulated_token_usage` 和 `token_usages`，两者在锁定 SDK 中包含同一批用量。`results/full/accounting_replay.json` 使用真实用量和安装的 SDK 重放原代码：72/72 个任务得到真实账本的 2 倍。现有兼容补丁将第二个 `if` 改为 `elif`，72/72 个任务恢复正确用量。

公开 Git 历史显示，SWE-QA 实验代码于 2026-03-08 首次加入；论文 v1 发布于 2026-01-23。公开证据尚不能确定论文表格是否使用上述重复累计代码。新版报告同时呈现真实 API 统计和公开代码的重复累计口径。统一倍数会改变绝对值，relative token change 保持原值。

## 已验证的推理偏差

旧推理为节约显存，省略了作者原始的 masked right padding。新阶段恢复每个 chunk 的 8192 长度 padding，保留经过验证的 query-axis tiled SDPA。重放使用历史轨迹的实际 query 和原始输出，同时比较旧实现、恢复 padding 后的实现与历史保留文本。逐例记录位于 `runs/full/diagnostics/padding/`，汇总写入 `results/full/padding_replay.json`。

目前已观察到 q30 一次长文件读取存在 1 行保留差异：恢复 padding 后移除原始观测第 3521 行的 `@dataclass`。诊断以全部重放完成后的统计为准。

## 端到端偏差的轨迹解释

上一轮 q11 的三个 pruner 执行均未提供剪枝 hint，因此该题完整保留了工具输出。其平均累计 tokens 约为 full 358.2K、pruner 520.4K；其余七题的事后合计差异约为 −3.1%。这说明 q11 的探索和上下文增长主导了八题均值的正向差异。原始八题总体仍作为历史结果完整保留。

论文 §3.2 和附录 J 明确将 hint 设为可选；附录 J 的 SWE-QA Bash 描述与当前工具提示一致。主实验继续沿用自主触发策略。固定轨迹压缩率用于解释 skimmer 的局部行为；端到端结果由完整任务的累计 API 用量衡量。

## 完整实验配置

- 全部 48 道公开 Streamlink 问题，3 次独立执行，full 与 pruner 共 288 次；随后完成 144 次 modification 对照。
- 使用与原文相同的 GLM-4.6 型号，固定 OpenRouter 的 Z.AI 路由；provider fallback 关闭。
- 原文 threshold=0.5、temperature=0、max rounds=250，发布 checkpoint、仓库 commit、工具提示词均锁定。
- 恢复作者 8192 padding；记录本地 SDPA、输出容量、时间上限、隔离 shell 和评委部署等可核实差异。
- 所有首轮轨迹、失败、重试、费用和答案保留。主分析覆盖全部题，另报告作者评分过滤规则与旧八题/新增四十题分层结果。
- 主表把论文结果、历史八题结果和新全题结果放在同一张表中。修改效果使用独立对照，quality change 使用相对百分比，机制成功率使用 SR%。

## 作者原始数据对照

作者 README 提供的公开 ZIP 已下载并核对，SHA-256 为 `eebd5c69165b46a753c82e23e9c082d9aaadb7532ed348bb886c2d267cf89c2b`。完整统计脚本为 `audit_paper_table.py`，逐行输出在 `results/full/author_table_audit.json`。

| 数据对象 | 原文 full/pruner tokens | 作者文件 input+output 均值 | 作者文件评分（同题过滤） | 作者文件轮数 |
|---|---:|---:|---:|---:|
| Streamlink / GLM-4.6 | 318.2K / 145.1K | 142.3K / 101.2K | 8.5628 / 8.5628 | 18.1875 / 24.9792 |
| Reflex / GLM-4.6 | 142.3K / 101.2K | 318.2K / 145.1K | 8.3733 / 8.2311 | 26.1250 / 36.6667 |

两仓库的 token 数值交叉对应，评分与轮数保持各自对应关系。这支持表 2 的 GLM token 列发生仓库错位。原文值和作者文件统计均保留为独立来源。Streamlink 的作者文件体现约 28.9% 的 token 下降。公开文件只提供聚合 token 字段，其与内部 API 账单的关系仍缺少原始响应验证。

作者 full 文件的 48 条 `token_cost` 均与同条 `prompt_tokens + completion_tokens` 存在差异；表格对照使用后两项和，并单独保留陈旧字段。评分通过作者公开过滤规则复算为 8.5628/8.5628，与论文 8.56/8.56 一致，分母为 43 个配对问题。

## 实际运行契约对照

作者轨迹的 system prompt 和完整工具 schema 与我们上一轮的真实 API 请求逐字一致，相关 diff 文件为空。作者实际使用 `azure/glm-4.6` 经 ByteDance gateway，当前可用路由为 OpenRouter/Z.AI。作者全部 996 次 Bash 调用都带非空 hint；这一策略差异在相同工具契约下出现，需要结合模型服务差异解释。

作者实际 shell 从共享根目录读取 `./swe-repos/conan`、`./swe-repos/reflex`、`./swe-repos/streamlink`，其配置记录 SWE-QA 最大步数为 50。新诊断恢复三仓库源码目录结构和 50 步上限。源码均使用作者指定 commits；评测答案与密钥留在 shell 外部。作者另有未公开的辅助文件，因此这个快照精确固定了已公开源码部分。

## 数值重放结果

旧实验全部 22 个剪枝观测成功精确重放。恢复 padding 后，6 个观测合计改变 8 个保留行判定。另从原八题各取作者首次超过 1000 字符的剪枝观测，共 8 个：5 个保留文本完全一致，3 个存在差异；全部源 tokenizer 计数一致。此结果将本地数值适配的影响量化到实际输入上。

## 当前进度与实验顺序

用户要求先在 subset 验证，再考虑扩展；总预算继续为 USD 12。新配置沿用最初八题，并先完整运行一轮 full/pruner，共 16 项。作者在同八题上的 input+output 均值为 190.2K/95.3K（约下降 49.9%）。先前选定的三道开发题在作者文件中反而上升约 60%，因此三题仅作为运行检查，原八题承担固定的端到端对照。

已启动的两项三题方案 baseline 保留于 `runs/full/formal`，并标记为开发阶段；后续任务已停止。新诊断源代码和协议位于 `revision_subset/`，全部证据保存在 `runs/subset/`。结果完成后再决定重复试验、行为差异消融和修改实验的顺序。
