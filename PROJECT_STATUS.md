# FTEC5660 SWE-Pruner reproduction

Deadline: 2026-11-10 24:00 Asia/Shanghai.

## Agreed scope
- Official SWE-QA multi-turn subset; full observations, original pruning, pruning with on-demand recovery.
- Three repetitions targeted; final sample count and budget follow pilot measurements.
- Pilot authorized up to USD 1. Formal experiment spending requires confirmation.
- Prefer user's OpenCode Go provider from CC Switch; verify endpoint and accounting first.
- English report <=10 pages, reproducible code/README/commits, raw evidence and figures, Chinese narration and demo script.
- User records presentation and submits. Public GitHub publication requires confirmation.

## Verified environment
- Upstream public commit: 96171b5f3ecaf89745cbeb436c8893b57f3400bd.
- Local upstream clone excluded from submission Git; preserve changes as patches or vendored attributed files.
- WSL Ubuntu-22.04 sees NVIDIA RTX 5060 Laptop GPU, 8151 MiB.
- WSL environment: /home/feifa/ftec5660-swe-pruner/.venv, Python 3.12.14.
- Torch 2.8.0 cu128 install started (exec session 95209).

## Evaluation requirements
- Separate pilot/development questions from fixed evaluation questions.
- Keep all selected tasks in primary results, including failures. Show author-filtered statistics separately.
- Count recovery and judge calls; preserve usage and timestamps.
- Record actual pruning, failures, repeated reads, and attention backend adaptations.
- OpenCode Go connectivity succeeded via official /inference/go/openai/v1, model deepseek-v4.1-flash. Response reports cash cost 0, billing_source go, allowance 0.00001782. Credential loaded from newest CC Switch opencode entry into ignored .env.
- Streamlink clone pinned to ab1f3656; official question JSONL includes reference answers. Task selection saved with source hash and seed; pilot and formal candidates disjoint.
- Official runner prepared with credential-safe config logging, serial execution, and user-agent/session headers.
- Live sessions: Torch install 95209; auxiliary dependencies 46358; model download 94597; SDK install 3620. Poll these handles before starting replacements.
- Observation store tests passed (2). Actual integration with OpenHands and model serving still pending.
- Model download completed: models/code-pruner/model.safetensors = 1345834856 bytes. Download session 94597 ended successfully; auxiliary session 46358 also completed.
- Added recovery_tool.py OpenHands integration and run_task.py isolated one-question process runner. These require SDK runtime validation before paid runs.
- Attention default adapted from flash_attention_2 to PyTorch SDPA for laptop portability, same across both pruner conditions. Must report this deviation and verify actual model output/peak memory; runtime validation pending.
- Remaining: budget-metered API transport before trial; SDK integration validation; model service launch; pilot and budget confirmation; formal runs; scoring and artifacts.
- Budget proxy implemented and verified with a metered OpenCode Go call. Running in WSL session 97483, port 8765; ledger runs/api_usage.jsonl; ceiling $1 conservative uncached peak-price accounting (including initial connectivity call).
- WSL inherited NO_PROXY patterns 127.* did not bypass httpx proxy; fixed exact loopback exceptions in runner and trust_env=False in pruning client.
- SDK install 3620 ended with PyPI TLS EOF. Retried via Tsinghua PyPI mirror, session 74458, currently running. Torch session 95209 remains running with download progress.
- Backbone config downloaded under models/qwen-backbone. Official paper Table 2 Streamlink reference values captured in configs/paper_reference.json.
- Separate lightweight Agent environment installed successfully: /home/feifa/ftec5660-swe-pruner/agent-env (SDK 1.1.0). Avoids GPU environment lock while Torch downloads.
- First baseline q43 r0 failed in upstream unconditional Claude HTTP monkeypatch before paid calls; process group 1132 terminated, logs retained. prepare_upstream.py now disables the patch for OpenAI-compatible route.
- Baseline q43 r1 running in session 63329 with real tool calls and metered API usage. Earlier parent session 63888 may now be terminal.
- Recovery runtime smoke passed: exact hello observation and Expand recovery, runs/recovery_smoke.json. Formal model-assisted recovery remains untested.
- Added scorer preserving exact official rubric via AST extraction, recording same-model judge limitation. Runtime score verification pending.
- Baseline q43 r1 completed: 68s, API input 33944/output 2295, Go allowance 0.00320133. Official rubric scoring succeeded (9.6 mean, same-model judge). Official runner double-counted usage by summing cumulative and individual metrics; patched second if to elif, API ledger authoritative.
- Baseline q26 r0 session 56558 and q17 r0 session 35192 running; network ConnectErrors conservatively charged at request bound. Pilot budget proxy remains active session 97483.
- GPU Torch download 95209 still progressing (~6.5GB cache); install chain 74458 now building editable swe-pruner. Server script ready but has not loaded weights yet.
