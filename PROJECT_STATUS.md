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
- User network preference: check download routes and aggregate size; downloads above 5 GB should preferentially use direct/SakuraCat rather than 魔戒. Current Clash profile GPT 分流 · 魔戒 + SakuraCat, rule mode; GPT 出口 -> 魔戒节点; 其余流量 -> SakuraCat 节点. No network-aware skill found in local skill catalogs.
- Reused existing C:/Users/feifa/.conda/envs/cuda312 GPU PyTorch 2.9.0.dev20250705+cu129 via isolated .venv-pruner --system-site-packages. Transformers 4.57.1 and serving dependencies installed there. Stopped WSL Torch download process 596 (session 95209) after GPU validation.
- Windows pruner server session 61845, PID 71968, health returns cuda:0 and SDPA. First tiny prune request exceeded 90 seconds; server still computing, investigate before restart. WSL server connectivity still to validate.
- Pilot q26/q17 ended with proxy budget 402 because ConnectError reservations accumulated. Ledger: 29 ConnectError entries reserve ~0.8426 USD; known request conservative cost ~0.1535 USD, cash 0, actual Go allowance ~0.0346 USD. Need reconcile transport failures while retaining original ledger before more trials.
- Transport accounting reconciled: ConnectError occurs before TLS/request transmission, so old conservative reservations are released on startup while original ledger rows remain intact. Other unknown transport outcomes retain bounds. Budget remains $1. Proxy now Windows port 8877, session 52025, PID 70104 (WSL TLS frequently failed). run_task/score_results use 8877.
- Windows pruner now session 85694, PID 70688, explicit BF16 (allocated weights 1268975616 bytes), source imports directly. Removed masked right-padding and unused attention weights for single-example inference; numerical equivalence check still pending before formal runs.
- Real-code smoke succeeded: albavision.py 6620 chars, 1687->169 tokens, ~2.0 sec, peak allocated ~2.88 GB; runs/pruner_real_code_smoke.json. WSL accesses Windows pruner through localhost:8000 successfully.
- Current serial pilot batch session 82827. pruner q43 r2 succeeded/scored 9.4, API total 183067, Go allowance .0087918; zero pruner service calls in that particular trajectory (must report bypass rather than claim compression). recovery q43 r0 ongoing, then baseline17/26 r1 and pruner/recovery17/26 r0. Failed earlier setup attempts retained.
- Pending: finish pilot, verify numerical equivalence of padding/attention optimizations, obtain formal budget approval, run formal fixed subset x3, score/analyze, generate/inspect report PDF and demo materials, publication-ready audit.

### Current download and network policy
- Before large downloads, inspect total dependency size, existing local installations, and actual Clash connection route. Prefer direct access or SakuraCat for transfers above 5 GB; avoid 魔戒 when a usable alternative exists.
- Existing CUDA-enabled PyTorch is now reused; GPU dependency installation/download was stopped. Model weights are complete. No additional >5 GB transfer is planned.
- Windows API proxy PID 70604 uses httpx trust_env=False after an explicit-proxy TLS failure and a successful direct-client probe. Current pilot resumed in session 73056; repeated-call reliability is still under observation.
- Recovery tool instructions now name the actual expand tool. Pilot skips existing validated score files to avoid duplicate judge calls.
- Numerical adaptation checks completed in validate_pruner.py: two fixed probes, original attention-weight computation and masked padding to 8192; all token threshold decisions agreed, max probability delta 0.0165281. Evidence runs/pruner_numerical_validation.json. This is a bounded sensitivity check, not a general equivalence guarantee.
- Deterministic component demo completed: demo.py, runs/demo.json; 1687 -> 169 tokens and exact line-range recovery. Two observation-store unit tests passed.
- Recovery q43 r1 completed (65.1s, 31174 tokens, official rubric mean10); baseline q17 r1 completed (46.93s, 95230 tokens, mean8). Pilot still active in session73056; baseline q26 r1 currently making successful calls. Known conservative total at latest ledger row ~0.4073 USD under $1 cap.
- Prepared configs/evaluation_protocol.md for 8 questions x3 conditions x3 repeats (72 scheduled attempts), preserving all failures and recording actual pruning activation. Formal approval remains pending.
