# 提交材料核对表

本表用于最终验收，运行过程中的状态以证据文件为准。课程要求提交报告、GitHub 链接和不超过 15 分钟的演示链接；本次工作范围交付本地可提交材料和 GitHub 待发布版本，用户负责录屏、确认发布及提交。

| 要求 | 验收证据 | 当前状态 |
|---|---|---|
| Instructor list 第 26 项 SWE-Pruner | 课程 PDF、README 来源链接、固定 upstream revision | 已核对 |
| 使用作者的可运行 pipeline | 官方 OpenHands runner、逐任务轨迹、API ledger | 已运行 |
| 复现明确报告目标并比较 | 官方 Table 2 参考值、本地 SWE-QA 结果、模型变化说明 | 已完成；72 次结果及 Table 2 对照见报告 |
| 单一主要修改与可测量影响 | 原始观测存储与 expand 接口、三组对照、恢复调用数 | 已完成；三组结果及 3 次自主恢复调用已记录 |
| 随机性重复 | 8 题 × 3 条件 × 3 次，固定 schedule，72 个 attempt | 已完成；72/72，三组各 24 次 |
| 英文报告最多 10 页 | 最终 report/SWE-Pruner_report.pdf、源稿、逐页渲染检查 | 已完成；最终 PDF 6 页，全部页面已检查 |
| 英文 README 与可复现步骤 | README、版本清单、模型哈希、运行命令 | 已编写及局部执行验证 |
| 修改以 commits 保留 | Git 历史、最终 bundle | 已完成；分步 commits 与 repository-history.bundle |
| 结果、图表和日志 | formal_tasks、formal_analysis、图表、evidence_audit、原始运行证据 | 已完成；最终分析与审计均无待处理项 |
| API 密钥隔离 | .gitignore、当前密钥内容检查、发布包扫描 | 打包脚本检查当前配置密钥及 Git 历史，交付 ZIP 自动校验 |
| 中文录屏讲解和 demo | demo_script_zh.md、demo.py、精确恢复记录 | 已完成；最终数字已写入，GPU demo 再次运行通过 |
| XJ13 可复用模块 | observation_store.py、recovery_tool.py、精确恢复与重叠读取测试 | 已完成 |
| GitHub 待发布版本 | 完整 ZIP、文件哈希、第三方许可、Git bundle | 最终包由 package_artifacts.py 生成，自动验证文件哈希与原始观测 |
| 姓名、学号 | 用户指定 Xia Feifan；最近 AIMS5701 HW4、AIMS5710 HW2 提交件均为 1155204948 | 已核对并补入 |

最终验收顺序：完成固定实验 → 补齐评分 → 审计证据 → 汇总统计 → 写结论 → 生成 PDF → 逐页检查 → 更新讲稿与 README → 提交代码 → 生成并验证最终包。

最终验收记录（2026-11-10）：72 次尝试全部执行，69 份有效导出答案全部评分；3 份截断评分完成补充，3 次流程失败原样保留。证据审计 pending=0、errors=0；5 项测试通过；数据版本、题目哈希及 9 个模型资源验证通过。报告 6 页，全部页面渲染检查完成。真实 GPU demo 再次验证 1687→169 tokens 与原文精确恢复。公开发布、录制及课程提交由用户完成。
