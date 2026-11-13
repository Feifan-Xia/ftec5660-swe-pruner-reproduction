# SWE-Pruner 子集复现诊断

## 当前完整结果

原协议 full/pruner/recovery 三组72项全部完成并通过 usage 完整性审计。Full/pruner 的平均tokens为136.4K/112.3K，下降17.6%；评分9.00/9.12，相对提高1.3%。作者公开运行记录中相同八题为190.2K/95.3K，下降49.9%；该参考来自作者自己的历史执行。本地实际剪枝覆盖25%，原作100%。

原始可选提示的恢复修改：评分相对pruner提高1.4%，tokens增加11.3%，质量区间跨零。24项恢复中12次成功读取均精确匹配并暴露新文本；7次超长、2次越界请求保留。必填提示24项诊断与72项机制实验完整完成，结果分别报告。

终止分支证据序列化缺陷已修复；两条同前缀重放保持原始版本，避免与自主重跑混淆。最新分析为 `results/full/manuscript_evidence.json`，双语终稿为 `report/revised/swe_pruner_reproduction_zh.pdf`（7页）和 `swe_pruner_reproduction_en.pdf`（7页）。余下40题的360项扩展方案已准备，USD24提案仍待批准，当前上限USD12。下文阶段表保留早期诊断时点，完整结果以上述文件为准。

## 研究对象与固定范围

复现对象为论文表 2 的 Streamlink × GLM-4.6 full/pruner 对照。OpenHands 是执行框架，SWE-QA 是问题、参考答案与评分流程，SWE-Pruner 对工具输出做任务相关剪枝。检验目标为累计 API tokens 下降并保持答案质量。用户要求先完成固定子集诊断，再考虑扩大题量；已批准总预算为 USD 12。

固定八题为 41、14、30、8、11、46、33、29，均在最初运行前选定。每个阶段保留相同集合、首轮轨迹、评分与失败证据。原先 72 次实验作为历史对照完整保存。

## 作者数据与论文表格核对

作者 README 提供的原始 ZIP SHA-256 为 `eebd5c69165b46a753c82e23e9c082d9aaadb7532ed348bb886c2d267cf89c2b`。其中有答案、评分、轨迹和配置，复算脚本为 `audit_paper_table.py`。

| GLM-4.6 数据对象 | 论文 full/pruner tokens | 作者 input+output 均值 | 作者过滤评分 | 作者轮数 |
| --- | ---: | ---: | ---: | ---: |
| Streamlink | 318.2K / 145.1K | 142.3K / 101.2K | 8.5628 / 8.5628 | 18.1875 / 24.9792 |
| Reflex | 142.3K / 101.2K | 318.2K / 145.1K | 8.3733 / 8.2311 | 26.1250 / 36.6667 |

两个仓库的 token 值交叉对应；评分和轮数保持各自对应。每个仓库的 48 道问题均精确匹配同名题库，与另一仓库交集为零，支持 GLM token 列存在仓库错位。两种来源分别保留。Streamlink 作者文件的节省率为 28.9%。作者 baseline 的 48 条 `token_cost` 均与 input+output 不一致，本次采用后者；作者聚合字段与内部 API 账单的关系仍缺少原始响应验证。

作者同一八题的 tokens 为 190.2K → 95.3K（−49.9%）。原始评分均值为 8.25 → 8.60；排除任一维度为 1 的配对题后，七题评分为 9.03 → 8.40。全文 8.56/8.56 使用 43 个配对问题。主结果保留全部本地固定题，作者过滤结果另列分母。

## 实现与统计修正

历史 72 个任务导出的累计 tokens 全部等于独立 API 账本。公开 runner 同时累计 SDK 的 `accumulated_token_usage` 与 `token_usages`，重放 72/72 得到账本的 2 倍。已有 `if/elif` 修复恢复正确值。公开 SWE-QA 代码提交晚于论文，其与论文计算实现的联系仍未确认。统一倍数保持相对变化方向。

作者轨迹的实际 SWE-QA 上限为 50 步，初始目录含 `./swe-repos/{conan,reflex,streamlink}`。当前阶段恢复这一目录布局、实际步数及固定 commits。作者未公开的辅助文件作为残余差异记录。Baseline 和 pruner 的 system prompt、完整 tool schemas 均与当前 API 请求精确一致。参考答案与密钥位于工具沙箱之外。

旧推理省略 masked right padding 并显式使用 BF16。恢复每块 8192 padding 后，历史 22 个剪枝观测中有 6 个观测合计改变 8 个保留行判定。作者服务默认加载 FP32，checkpoint 含 15 个 FP32 tensors；旧 BF16 强制转换会舍入这些参数。当前恢复 FP32。固定八题各取作者首次超过 1000 字符的观测，精确剪枝文本匹配从 5/8 提升为 7/8；源 tokenizer 计数全部一致。残余 q30 的保留 tokens 为作者 982、本地 920。原融合注意力算术诊断得到与 FP32 SDPA 相同的文本。

当前 GPU 服务使用 query-axis tiled SDPA，完整保留 key/value 注意力范围，峰值约 6.5 GiB。原硬件与 FlashAttention 内核仍有差异。固定输入重放量化数值适配影响；独立在线运行的均值变化还包含调查路径波动。

精度术语：FP32 指权重加载精度。发布代码的前向计算采用 FP16 autocast，再把 logits 转回 FP32；本地保留该处理。旧显式 BF16 转换主要额外舍入 checkpoint 中原本为 FP32 的 15 个 tensors。

## 触发策略与独立修改

作者通过 ByteDance gateway 使用 `azure/glm-4.6`，本地使用 OpenRouter/Z.AI。相同工具契约下，作者全部 996 次 Bash action 带非空 hint，旧本地 pruner 的 24 次任务仅 10 次触发。目录/padding 修正后的 BF16 首轮仅 1/8 任务触发。

三道独立开发题上，默认、开启 reasoning、关闭 reasoning 的九次首轮请求均省略 hint，尚未执行任何命令。只将 hint 字段设为必填的三次探针全部生成 hint。因此 `revision_hint/` 仅把该 action 字段改为必填非空字符串并同步说明，其他执行、模型、提示词、数值推理和评分保持一致。AST 与 schema 隔离检查通过。这组明确标记为策略修改，保留原始 optional-hint 对照。

## 阶段结果

| 阶段 | 范围 | full/pruner tokens | full/pruner 评分 | 剪枝任务 |
| --- | --- | ---: | ---: | ---: |
| 历史配置 | 8 题 × 3 次 | 112.8K / 131.0K | 8.63 / 9.27 | 10/24 |
| 目录、步数、padding 修正，BF16 | 8 题 × 1 次 | 103.8K / 89.0K | 9.55 / 8.90 | 1/8 |
| 同上，恢复 FP32 | 8 题 × 1 次，16/16 完成 | 119.9K / 86.6K | 9.15 / 9.00 | 1/8 |
| FP32＋必填 hint | 首轮进行中 | 完成后统计 | 完成后统计 | 完成后统计 |

BF16 修正阶段的 token 变化为 −14.3%，评分变化为 −6.8%；八题 bootstrap 的 token 区间跨零。该阶段的单次结果支持继续检查触发覆盖与重复执行稳定性。原始观测存储与恢复扩展及其历史 72 次机制实验继续单列，最终报告会分别分析每个实验的作用和代价。

FP32 首轮 token 变化为 −27.7%（八题 cluster bootstrap 95% 区间 −41.7% 至 +14.0%），评分变化为 −1.6%（−4.5% 至 +1.3%）。实际剪枝覆盖仍为 12.5%。原冻结配置正在补齐三次重复，以区分稳定节省与调查路径波动。

三道开发题的 Novita/BF16 首轮探针均省略 hint，实际费用 USD 0.00445126。这一诊断提供跨部署精度的观察，后续正式运行继续固定 Z.AI。另用本地假响应重建发布 SDK 的 Azure 发送路径，确认 temperature=0、top_p=1，hint 保持可选，发出的工具 schema 与作者轨迹精确一致（`azure_wire_contract.json`）。

## 冻结配置文字勘误

`revision_precision/protocol.json` 的 `primary_analysis` 沿用了早期全题方案的 “48 paired question clusters”。同文件 indices、population 和实际 bootstrap 均为八题。冻结源文件保留原样；当前分析严格使用八个 question clusters。
