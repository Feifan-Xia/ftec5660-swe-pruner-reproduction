"""Bilingual gap evidence from the complete author-observation replay."""
import json
from pathlib import Path
ROOT = Path(__file__).resolve().parents[2]
r = json.loads((ROOT / "results/full/author_all_observations_replay.json").read_text(encoding="utf-8"))["summary"]

ZH_FIDELITY = f"""进一步重放同一八题全部 131 条作者剪枝观测，保留原始文本、hint、短输出和未改变输出，127 条输出逐字一致（{100*r['exact_text_count']/r['n']:.1f}%）。

| 固定输入指标 | 作者记录 | 本地重放 |
|---|---:|---:|
| 原始 tokens | {r['author_raw']:,} | {r['local_raw']:,} |
| 保留 tokens | {r['author_kept']:,} | {r['local_kept']:,} |
| 文本压缩率 | {r['author_compression_percent']:.2f}% | {r['local_compression_percent']:.2f}% |

表 1a. 同一八题全部作者输入逐条重放。131/131 完成，服务失败为零，四条残余差异保存逐行 diff。压缩率相差 0.014 个百分点，支持当前实现对已知作者输入的高度一致性。自主运行的剩余排查重点为实际 hint、命令和重读路径。"""

EN_FIDELITY = f"""Replaying all 131 saved pruning observations from the same eight questions, with original text and hints including short and unchanged outputs, produces 127 exact text matches ({100*r['exact_text_count']/r['n']:.1f}%).

| Fixed-input measure | Author record | Local replay |
|---|---:|---:|
| Source tokens | {r['author_raw']:,} | {r['local_raw']:,} |
| Retained tokens | {r['author_kept']:,} | {r['local_kept']:,} |
| Text compression | {r['author_compression_percent']:.2f}% | {r['local_compression_percent']:.2f}% |

Table 1a. Complete same-input skimmer replay: 131/131 completed, zero service failures. Line diffs retain four residual disagreements. The compression difference is 0.014 percentage points. This establishes close component fidelity on known author inputs and focuses the online diagnosis on hint use, commands and rereading."""

ZH_TRAJECTORY = """完整三重复中，本地累计 tokens 下降 17.6%，请求数下降 17.7%，每请求平均 tokens 增加 0.1%。当前整体节省主要体现为路径变短，对持续上下文剪枝的支持较弱。作者同一八题 131/131 次 Bash 使用 hint，本地为 6/254 次（2.4%）；按任务统计分别为 100% 与 25%。

作者 full 在八题中有九次命令超时、涉及四题，pruner 有一次；本地两组均为零。作者 q41 full 经过四次超时后反复在 Conan 中寻找 Streamlink 的 TestIO，达到 50 步，评分 2.8；本地三次平均评分为 8.67，tokens 为 32.3K，作者为 146.2K。作者 q8 full 也有三次超时和跨仓库探索，193.8K 对应本地 43.3K。轨迹支持额外搜索与失败成本这一过程解释；各因素的独立因果份额仍需控制实验。所有题目与失败保留在汇总中。"""

EN_TRAJECTORY = """Across all three repetitions, the local 17.6% token reduction factorizes into 17.7% fewer API requests and 0.1% more tokens per request. The aggregate benefit primarily reflects shorter paths, with limited evidence of sustained context reduction. Local optional pruning uses hints in 6/254 Bash actions (2.4%), versus 131/131 in the authors' same-question records; task-level activation is 25% versus 100%.

Author full trajectories contain nine command timeouts across four questions, versus one in their pruning arm and zero in both local arms. In q41, four timeouts precede repeated searches for Streamlink's TestIO inside Conan; author full reaches 50 steps and scores 2.8, while local mean quality is 8.67 and usage is 32.3K versus 146.2K. Author full q8 has three timeouts and cross-repository search, using 193.8K versus 43.3K locally. These traces identify additional search and failure costs; independent causal contributions require controlled intervention. All tasks and failures remain included."""

ZH_DEVELOPMENT = """### 5.4 首次提示引导的开发实验

在与固定八题分离的三道开发题（43、26、17）上，仅首次 API 请求要求非空 hint，后续恢复原始可选字段。full 与 pruner 使用相同接口与引导，区别为执行器是否过滤输出。六项均完成，后续提示触发为 3/3；逐请求 schema 审计通过。

| 开发实验指标 | 匹配 full | 首次引导 pruner | 相对变化 |
|---|---:|---:|---:|
| 平均累计 tokens K | 102.5 | 63.9 | −37.7% |
| 平均质量 / 10 | 9.07 | 8.13 | −10.3% |
| 平均 API 请求数 | 9.67 | 8.67 | −10.3% |

表 6. 三题单重复的策略开发结果。q43、q26、q17 的 full/pruner 评分分别为 10/10、9.2/7.0、8.0/7.4。质量降幅超过预设 2% 容忍值，该候选停止进入固定八题确认。q26、q17 各有三次缺失用量回执的网络失败；修复传输后第四次首次完整执行入表，所有失败保留，运行期网络差异属于额外限制。

源码核查发现两处参考答案偏差：q17 把正常的 Fetch.failRequest 回退描述为抛出 CDPError 并终止会话；固定源码和测试支持阻止请求的行为。q26 把 HTML 上的 main_js_url_re 与随后下载 JavaScript 上的 user_id_re 描述为扫描同一 JS 内容；生成答案也包含缺少验证的回溯复杂度推断。官方评分与失败判定保持原值，源码片段及哈希保存在 development_reference_audit.json。质量差距包含答案覆盖与评测参考偏差，三题结果尚不足以支持质量保持。

"""

EN_DEVELOPMENT = """### 5.4 First-request priming development screen

Three disjoint development questions (43, 26, 17) require a nonempty hint only on the first API request, then restore the original optional schema. Matched full and pruner use identical interfaces and priming; only executor filtering differs. All six cells complete, all three pruning tasks use later hints, and request-level schema checks pass.

| Development measure | Matched full | Primed pruner | Relative change |
|---|---:|---:|---:|
| Mean cumulative tokens K | 102.5 | 63.9 | −37.7% |
| Mean quality / 10 | 9.07 | 8.13 | −10.3% |
| Mean API requests | 9.67 | 8.67 | −10.3% |

Table 6. One repetition per development question. Full/pruner scores are 10/10, 9.2/7.0 and 8.0/7.4. The quality decline exceeds the predeclared 2% tolerance, stopping fixed-eight confirmation of this candidate. Both q26 and q17 require three preserved transport failures before their first complete, receipt-backed fourth execution; transport changes add a run-period limitation.

A source audit identifies reference disagreements: q17 describes normal Fetch.failRequest fallback as raising CDPError and terminating the session, whereas the pinned code and test support blocking the request. For q26, main_js_url_re scans HTML before a separate JavaScript response is searched with user_id_re; the reference describes both scanning the same JS content. Generated answers also contain unsupported regex-complexity claims. Official scores and the failed gate remain unchanged. Source excerpts and hashes are retained in development_reference_audit.json. This screen provides insufficient evidence of quality preservation.

"""
