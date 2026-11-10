# FTEC5660 最终材料验收

2026-11-11 · Xia Feifan · 1155204948

- GLM-4.6 固定 Z.AI 主实验：72/72 完成，三组首轮均 24/24 答案，独立 GPT-5 评分完成。
- 单一主要修改：任务级观测存储与精确范围恢复；固定上下文机制测试 72/72 完成。
- 结果分析：原文 Table 2 对照、逐题变化、剪枝触发、恢复行为、评分敏感性和失败处理已写入中英文报告。
- 报告：report/glm/SWE-Pruner_report_zh.pdf 与 SWE-Pruner_report_en.pdf，均 8 页；16 页全部渲染检查。
- 验证：5 项核心测试、2 项 WSL 兼容/隔离测试及 attention mask/causal 测试通过；641 个仓库文件与 2 个符号链接匹配固定版本。
- 完整性：results/glm/audit.json 为 PASS；15 个冻结源文件、逐请求 provider、评分来源、原始观测和读取范围均核验。
- 费用：固定路由已报告 $2.56655245；全项目保守账本 $7.92620608，批准上限 $12。一次评分传输失败的保守占用保留。
- 演示：demo_script_zh.md；python revision_glm/demo_recovery.py 已执行通过。
- 最终打包：revision_glm/package.py 包含文件哈希、Git bundle、许可证和原始证据，并扫描配置密钥、校验 ZIP。

学生后续操作：按讲稿录制不超过 15 分钟的视频，确认 GitHub 发布与视频访问权限，再提交报告和链接。
