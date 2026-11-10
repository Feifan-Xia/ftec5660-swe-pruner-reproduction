# 调试记录

- 上游固定到 `96171b5f3ecaf89745cbeb436c8893b57f3400bd`，Streamlink 固定到 `ab1f3656`。
- WSL Ubuntu 22.04 可见 RTX 5060 Laptop 8 GB；Python 3.12.14。GPU 环境下载较慢，因此将 OpenHands 单独安装到 agent-env，先执行基线开发题。
- 官方 main.py 无条件启用 Claude HTTP monkeypatch，OpenAI-compatible 运行在发送请求前出现 NoneType.status_code；关闭该补丁后工具循环正常。
- WSL 的 NO_PROXY 使用 127.*，httpx 本地请求仍走代理并返回 502。改为 localhost、127.0.0.1、::1；剪枝客户端显式 trust_env=False。
- 官方 token 汇总同时累加 accumulated_token_usage 与 token_usages，首个成功开发题输出恰为 API 账本的两倍。将第二段 if 改为 elif；所有结果以代理逐请求 usage 为主依据。
- 模型 attention backend 设为 SDPA，保留发布权重与剪枝阈值。Windows 服务复用已有 CUDA PyTorch 环境；真实代码 demo 已测得 1687→169 tokens，两组数值探针的 0.4 阈值保留决策一致。
- 开发题 q43 基线运行成功，耗时约 68 秒，API 输入 33944、输出 2295 tokens。参考答案对照评分 9.6/10 来自同模型 judge，属于开发题结果。
- 正式 recovery q14 r0 达到迭代上限后，兜底客户端误用 SDK 模型前缀并遗漏 session header。修复后归档 V1/V2，首 6 次运行保留 V1；该失败保留在原定 72 次中。
- baseline q33 r1 的 FinishAction.message 已生成完整答案，SDK action.name 为 null 导致作者提取器漏导出。原始空答案和评分保留，审计额外比较导出答案与 FinishAction。
- pruner q11 r2 的兜底请求将全部 4096 completion tokens 用于推理，最终答案为空；费用与失败保留。
- 初始 judge 的 2048-token 上限可能在 JSON 完成前截断输出；仅对缺失评分执行最多两次 4096-token 补评分，保留初始响应和有效原评分。
- 发布包逐字保留 runs/ 原始证据，并验证每个文件哈希、观测内容 ID 与恢复字符数。英文报告包含完整环境差异和失败解释。
