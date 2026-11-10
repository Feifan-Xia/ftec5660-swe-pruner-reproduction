# 提交材料核对表

本表用于最终验收，运行过程中的状态以证据文件为准。课程要求提交报告、GitHub 链接和不超过 15 分钟的演示链接；本次工作范围交付本地可提交材料和 GitHub 待发布版本，用户负责录屏、确认发布及提交。

| 要求 | 验收证据 | 当前状态 |
|---|---|---|
| Instructor list 第 26 项 SWE-Pruner | 课程 PDF、README 来源链接、固定 upstream revision | 已核对 |
| 使用作者的可运行 pipeline | 官方 OpenHands runner、逐任务轨迹、API ledger | 已运行 |
| 复现明确报告目标并比较 | 官方 Table 2 参考值、本地 SWE-QA 结果、模型变化说明 | 正式结果收集中 |
| 单一主要修改与可测量影响 | 原始观测存储与 expand 接口、三组对照、恢复调用数 | 代码完成，正式对照待汇总 |
| 随机性重复 | 8 题 × 3 条件 × 3 次，固定 schedule，72 个 attempt | 运行中 |
| 英文报告最多 10 页 | 最终 report/SWE-Pruner_report.pdf、源稿、逐页渲染检查 | 草稿已检查，最终版待生成 |
| 英文 README 与可复现步骤 | README、版本清单、模型哈希、运行命令 | 已编写及局部执行验证 |
| 修改以 commits 保留 | Git 历史、最终 bundle | 本地提交已保留 |
| 结果、图表和日志 | formal_tasks、formal_analysis、图表、evidence_audit、原始运行证据 | 自动生成流程已验证 |
| API 密钥隔离 | .gitignore、当前密钥内容检查、发布包扫描 | 当前检查通过，最终包再验 |
| 中文录屏讲解和 demo | demo_script_zh.md、demo.py、精确恢复记录 | 已完成，结果数字待更新 |
| XJ13 可复用模块 | observation_store.py、recovery_tool.py、精确恢复与重叠读取测试 | 已完成 |
| GitHub 待发布版本 | 完整 ZIP、文件哈希、第三方许可、Git bundle | 打包流程已验证，最终包待生成 |
| 姓名、学号 | 同课程既有作业确认英文署名 Feifan Xia；学号收到后补入 | 姓名已补，学号等待回复 |

最终验收顺序：完成固定实验 → 补齐评分 → 审计证据 → 汇总统计 → 写结论 → 生成 PDF → 逐页检查 → 更新讲稿与 README → 提交代码 → 生成并验证最终包。
