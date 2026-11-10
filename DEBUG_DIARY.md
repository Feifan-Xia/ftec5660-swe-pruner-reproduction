# 调试记录

- 上游固定到 `96171b5f3ecaf89745cbeb436c8893b57f3400bd`，Streamlink 固定到 `ab1f3656`。
- WSL Ubuntu 22.04 可见 RTX 5060 Laptop 8 GB；Python 3.12.14。GPU 环境下载较慢，因此将 OpenHands 单独安装到 agent-env，先执行基线开发题。
- 官方 main.py 无条件启用 Claude HTTP monkeypatch，OpenAI-compatible 运行在发送请求前出现 NoneType.status_code；关闭该补丁后工具循环正常。
- WSL 的 NO_PROXY 使用 127.*，httpx 本地请求仍走代理并返回 502。改为 localhost、127.0.0.1、::1；剪枝客户端显式 trust_env=False。
- 官方 token 汇总同时累加 accumulated_token_usage 与 token_usages，首个成功开发题输出恰为 API 账本的两倍。将第二段 if 改为 elif；所有结果以代理逐请求 usage 为主依据。
- 模型 attention backend 设为 SDPA，保留发布权重与剪枝阈值。实际剪枝服务验证仍待完成。
- 开发题 q43 基线运行成功，耗时约 68 秒，API 输入 33944、输出 2295 tokens。参考答案对照评分 9.6/10 来自同模型 judge，属于开发题结果。
