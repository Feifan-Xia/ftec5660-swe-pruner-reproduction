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
- Formal runner now generates 72 unique counterbalanced jobs, validates explicit approval scope, preserves existing attempts, and stops on an exhausted proxy budget. run_task refuses overwriting an existing task.
- Budget proposal based on first five successful pilots was sent for user approval: total project cap $8 including pilot, 72 formal tasks; mean estimate $2.35 agent + $0.22 judge. Approval still pending. Later pilot tasks will update the estimate; the proxy retains the original $1 ceiling until explicit approval.
- Recovery q17 r0 produced two real pruned observations (978->540 and 2223->654 tokens). No expand call was made in that run. Component demo remains separately labeled.
- Added report/report.md and report/build_report.py; generated a three-page DRAFT and visually checked all pages. Formal results and conclusions remain explicitly pending. Added demo_script_zh.md with 10-12 minute recording guidance.
- Added formal aggregation/paired question-bootstrap analysis code and installed environment manifests. Numerical/runtime outputs are still local under ignored runs; reviewed public evidence packaging is pending.
- User explicitly approved project total conservative budget $8 and all 72 formal runs. Authorization saved in configs/formal_approval.json. Existing pilot proxy still has $1 cap until idle restart; formal launch follows pilot completion.
- Added pinned agent requirements, selected GPU dependencies, portable WSL setup, exact model revision/file hashes, and expanded README commands. Historical nightly GPU runtime availability is disclosed.
- Added local reviewed bundle generation with exact credential checks, path normalization, file hashes, and third-party license copies. No publication performed.
- Analysis validation uses a hand-computed 72-row fixture with one failure: expected denominators, failure-zero score, and paired token effects passed. Total three tests passed.
- All nine planned pilot condition/question combinations completed and were scored. Successful-task average conservative cost is $0.0505065; mean wall time 160.41s. Project cumulative conservative usage including troubleshooting and judges is $0.7477503. Final pilot implies ~3.21h for 72 serial agent runs and ~$3.64 agent cost, before judging; $8 approved cap remains enforced.
- Budget proxy restarted after terminal pilot session73056, now session13542, port8877, limit$8, prior usage carried forward. Records now include nonsecret decoding parameters.
- Formal schedule launched with run_formal.py after pilot completion. Fixed eight-question x3-condition x3-repeat plan; collect authoritative process handle in next status update.
- Pilot actual activation: two pruned observations in recovery q17; zero expansion calls across nine successful pilot runs. Preserve optional official focus-query mechanism and report activation rates.
- Formal session24992 is active; first two attempts completed and scored. Runtime/config hashes frozen under runs/formal/runtime_manifest.json after first task, with no intervening runtime change.
- Added evidence audit for approved schedule, frozen runtime, question-only agent input, score arithmetic, trajectory/provider-usage presence, and total budget. Initial audit: 72 scheduled, 70 pending, zero errors, conservative usage$0.7775388.
- Actual formal outgoing decoding parameters are temperature0.0, top_p1.0, max_tokens4096 (SDK resolves unspecified temperature). Report corrected to use transmitted settings. Judge requests use temperature0/max_tokens2048.
- Final pilot measurements saved separately from historical approval estimate. Formal packaging now requires clean tracked files and successful evidence audit, and includes the reviewed conclusion and audit outputs.
- Real partial formal outputs successfully passed analysis and draft PDF generation (4 pages), with missing repeat intervals labeled pending. Final report remains gated on all attempts and reviewed conclusion.
- Added report robustness for unavailable statistics and explicit per-condition timing/Go allowance/conservative cost tables. These reporting changes leave the frozen experiment runtime unchanged.
- Formal run continues in session24992; q41 all three conditions completed/scored. q14 pruner is active with ongoing successful API calls. Cumulative conservative usage latest observed ~$0.9585.
- Confirmed formal recovery q14 r0 reached 30 steps, then fallback direct client used openai/ model prefix and omitted task session headers; proxy rejected it. Primary attempt retained as failed, judge score1.0. No replacement run introduced.
- Temporarily stopped only scheduler PID3122 while already-started baseline q14 r0 finished under V1. Patched fallback canonical model and headers via prepare_upstream.py, tested actual extracted function with recording API stub (4 tests pass). Resumed scheduler with SIGCONT.
- Exact prior main.py reconstructed and SHA verified against original runtime manifest; archived V1/V2 sources and V1 manifest. Current manifest records first six tasks as V1, remaining66 as V2. Source/model/prompts/limits/threshold/judge otherwise unchanged. Report and protocol disclose amendment and retained failure.
- Formal process remains session24992; budget proxy13542 and pruner85694 remain running. Latest audited total ~$1.223, 5 completed/scored plus baseline q14 scoring pending at audit time.
- Formal progress: 8/72 attempts resolved, evidence audit zero errors, latest conservative total ~$1.32265. Scheduler session24992 remains live.
- Added observation-level timeout counts and pruner-token retention totals to aggregation/reporting. Documented authors' ten-second Bash timeout and filtered-clone historical-object/network caveat. Runtime conditions unchanged; four tests pass.
- Added formal task elapsed time from original task.json/exit.json write timestamps, captured once in measurement_timing.json for portability. This includes failed attempts and excludes judging; inner author timing retained separately. Four tests passed.
- Added scripts/freeze_runtime.py for fresh reproductions and documented invocation. Capture smoke matched all13 current raw hashes. Added canonical LF hashes to current manifest and audit so Windows/Linux line endings alone do not invalidate code identity; runtime source files unchanged.
- Latest formal audit: 14/72 resolved, zero errors, conservative usage ~$1.76508. Name Feifan Xia verified from same-course HW2 cover; student ID query remains pending.
- Formal recovery q46 r0 completed but initial judge response used all2048 tokens for reasoning, finish_reason=length, empty JSON content. Initial response preserved; scoring pending while main scheduler continues.
- Added repair_scores.py for post-run missing-score repair only: identical official rubric/model/temp0, output cap4096, at most2 additional preserved attempts. Valid existing scores remain unchanged. No repair calls made yet; execute after formal agent runs to keep timing separate. README/report disclose policy; initial frozen scorer remains unchanged.
- Report readability pass: body10.5pt/14.5 leading, table8.5pt, intact tables/figure captions and guarded Results page break; current draft5 pages. Inspected changed results pages; final PDF will receive full-page review after results complete.
- Live fallback repair verified: recovery q11 r0 and baseline q11 r0 both reached30 iterations and successfully sent temperature0.3 canonical-model requests under their correct task sessions (status200). No extra smoke request needed.
- Clarified agent iterations versus batched tool actions: pruner q11 had26 API calls and43 observations, including26 pruning activations. Actual mechanism counts are now included in report tables.
- First formal repetition completed:24 attempts,23 valid answers,23 saved scores including the retained failure; recovery q46 r0 judge remains pending. Snapshot results/first_repeat_snapshot.json.
- First-repeat agent conservative cost$1.4378088, observed judge$0.0403395; extrapolated total including pilot ~$5.1822, within approved$8 cap. Summed agent task elapsed3157.19s (~52.6min), plus judging/inter-task overhead. Main scheduler continues remaining two repetitions.
- Verified Python Random(5660) shuffled indices exactly reconstruct the frozen pilot/candidate selection; README now records the procedure.
- Formal recovery q41 r1 autonomously expanded lines1-29 after an851-to6-token pruning result. Recorded payload equals the full original1570-character output; manifest has one read, zero repeated lines. Answer scored10, task101923tokens. Added evidence-linked case and Chinese narration; causal benefit remains untested without controlled replay.
- Report now displays failure-zero score beside repeat variability and requires resolved audit/repair summaries for final build. Updated draft is6pages; changed metric table visually checked. Final all-page review remains pending.
- Packaging now byte-preserves all raw runs/ evidence, including local paths, so content-addressed IDs and read lengths remain verifiable. Other text retains path normalization. Draft ZIP194file hashes verified;132pilot files match source bytes;48observation content IDs validated. Final package remains pending formal completion.
- Second repetition complete at19:05:48/72attempts,46valid exported answers,46score files including two failed exports; two valid-answer judge repairs remain pending. Conservative project usage$3.194489; third repetition continues in session24992. One autonomous expansion observed so far.
- Added exact-command review for recovery/q11_r1 grep with ../../: explicit nested cd resolves search to repository src/streamlink. Raw flag and reasoning preserved in configs/command_access_reviews.json; unmatched flags still require review.
- Baseline q33 r1 has an empty exported answer despite a2839-character FinishAction.message. Author extractor checks action.name, which is null for this SDK action; eight actions do not trigger fallback. Primary failure and original judge1 retained. Added report/case note; audit now compares saved answers with FinishAction messages. At48attempts this is the only mismatch. Final case-note sentence about then-completed comparison should be updated after72.
- User specified cover name Xia Feifan. Student ID1155204948 verified consistently in recent AIMS5701 HW4 submission and AIMS5710 HW2 with-AI submission. Report source and checklist updated; identity metadata is resolved.
