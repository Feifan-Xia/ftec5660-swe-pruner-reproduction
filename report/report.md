# SWE-Pruner on SWE-QA: A Laptop Reproduction with Recoverable Tool Observations

Xia Feifan | Student ID: 1155204948

FTEC5660 — Individual Reproducibility Project | 10 November 2026

## 1. Target and scope

SWE-Pruner reduces the code context returned by tools to a coding agent. A released small model scores code tokens against a focus query, allowing the agent to retain relevant fragments while continuing a multi-step repository investigation. This project targets the SWE-QA Streamlink experiment in Table 2 of the paper [1], using the authors' OpenHands evaluation pipeline [2]. The central measurement is the trade-off between answer quality and cumulative LLM input/output tokens.

The reproduction uses a fixed subset of the authors' 48 Streamlink questions. It compares full tool observations, the authors' optional focus-conditioned pruning, and pruning with an added tool for exact recovery of saved observations. The latter is the isolated experimental modification. The study also verifies the released checkpoint's pruning behavior directly and records the operational changes needed to run it on an 8 GB laptop GPU.

The underlying agent is DeepSeek V4.1 Flash through OpenCode Go. The paper reports Claude Sonnet 4.5 and GLM-4.6. Published scores therefore provide context; the paired local conditions provide the comparison for this reproduction. Model choice, sample size, inference backend, and execution limits constrain any quantitative replication claim.

## 2. Setup and reproducibility controls

The authors' repository is pinned to commit 96171b5f3ecaf89745cbeb436c8893b57f3400bd. Streamlink is checked out at ab1f3656. The question JSONL has SHA-256 af5d149b7a256b85d50c0d5971f42c3504f14f97632708bb06c1d486c6db0162. Selection seed 5660 partitions development indices 43, 26, and 17 from the formal candidate list. Only the question text is passed to the answering agent; reference answers are reserved for scoring.

The Bash tool retains local filesystem permissions. Recorded shell commands are audited for direct references to known question/answer artifact paths, alongside exact checks of the question-only input files. The audit documents observed access and input construction; it does not establish filesystem isolation.

The GPU is an NVIDIA RTX 5060 Laptop with 8,151 MiB VRAM and driver 591.59. The pruner service runs on Windows using the existing PyTorch 2.9.0.dev20250705+cu129 environment, Transformers 4.57.1, and the released ayanami-kitasan/code-pruner checkpoint (1,345,834,856-byte weights file). A lightweight WSL Ubuntu 22.04 Python 3.12 environment runs OpenHands SDK 1.1.0. Mirrored localhost networking connects the agent, the local pruner service, and an API budget proxy.

The authors' Bash executor imposes a ten-second timeout on each shell command. Such tool failures are counted separately from whole-task execution failures because the agent may recover and still answer. Streamlink was cloned with blob filtering; historical objects can require on-demand network access. Tool latency and history availability therefore depend partly on local cache and network state, which also affect timing comparisons.

The agent provider endpoint is https://opencode.ai/inference/go/openai/v1; credentials remain in a local ignored environment file. The first formal requests record the effective outgoing temperature as 0.0, top_p as 1.0, and maximum output as 4,096 tokens per request. The SDK configuration leaves temperature unspecified, so the transmitted request is the authoritative setting. The authors' fallback answer generation uses temperature 0.3. All conditions share these settings, a 30-step limit, a 600-second question limit, and pruning threshold 0.4. Repetition measures observed run-to-run variation, including provider and tool behavior under these settings.

For laptop inference, SDPA replaces Flash Attention, unused attention weights are omitted, and masked right-padding is removed for single-example inputs. Weights are stored in BF16; the authors' FP16 autocast is retained. Two fixed probes compared attention-weight calculation and masked padding, including padding to 8,192 positions. All 0.4-threshold token decisions agreed, while the largest token-probability difference was 0.01653. This sensitivity check supports the tested examples; broader numerical equivalence remains an open limitation.

## 3. Conditions, metrics, and analysis

The baseline uses the authors' full-output Bash tool. The pruner condition exposes the authors' context_focus_question argument: pruning activates when the agent supplies it. Consequently, assignment to the pruner condition and actual pruning activation are separately measured. The recovery condition preserves that mechanism and adds an observation ID, original line count, and an expand tool. The store retains the original string and returns inclusive, one-based line ranges, capped at 200 lines per request. Reads and repeated lines are logged. Each task has an independent store.

The 30-iteration cap applies to agent turns; a turn can contain several tool actions. Tool-observation counts can therefore exceed 30, and an additional fallback answer request can occur after the cap. Both resource use and tool activations are counted from the actual records.

The formal design uses eight disjoint questions, three conditions, and three repetitions. Condition order rotates by question and repetition to distribute temporal drift. Every scheduled attempt remains in the inventory. Completion rate includes failures; resource measurements include all API requests attributable to the attempt. Answer-score summaries state their completed-answer denominator, with a failure-assigned zero-score sensitivity analysis. The authors' score-filtered analysis is secondary.

The official rubric evaluates correctness, completeness, relevance, clarity, and reasoning on integer scales from 1 to 10. The task score is the mean of these five dimensions. The judge uses temperature 0, the official prompt, and the same DeepSeek model as the answering agent. This maintains a consistent evaluator across conditions but introduces same-model evaluation bias. The small subset and absence of independent human grading limit generalization.

Initial judge requests allow 2,048 output tokens. A reasoning-only response exhausted that budget before emitting JSON. Missing or invalid scores therefore receive up to two repair attempts with a 4,096-token ceiling, retaining the same rubric, model and temperature. Initial responses and repair usage are preserved; valid scores are retained unchanged. Repair counts and any unresolved scores are documented with the final evidence.

Cumulative tokens come from provider usage records for each request, with judge calls separated by session ID. Input tokens include cached prompt tokens; output tokens include provider-reported reasoning usage. Cash charges, Go allowance consumption, and conservative uncached peak-price accounting are reported separately. Task elapsed time is reconstructed once from the original local task.json and exit.json write timestamps, then saved in a timing sidecar. It includes process startup, tools, API latency and cleanup, covers failed attempts, and excludes judging. The authors' completed-answer time is retained separately. Pruning activations and recovery calls establish whether the mechanisms were used. Repeat-level means and dispersion describe stochastic variation; paired question-level comparisons average repetitions within each question.

## 4. Results

{{RESULTS}}

### A trace-level check

For question 41, repetition 0, all three conditions correctly located TestIO.test_load_data and its cache._dirty assertion, matching the reference's central location. Each received a 10.0 mean rubric score. Cumulative tokens were 36,663 for baseline, 46,492 for pruner, and 36,787 for recovery. None of these three trajectories activated pruning or expansion. Thus, this instance demonstrates repository question answering and variability between trajectories; it supplies no instance-level evidence that compression caused the token difference. Evidence-linked case notes are included with the artifacts. This inspection is AI-assisted rather than an independent human evaluation.

### Released-checkpoint behavior and exact recovery

A formal autonomous recovery occurred on question 41, repetition 1. Pruning reduced a 29-line repository search result from 851 source tokens to 6, leaving only a filtered-lines marker. The agent immediately called expand for all 29 saved lines, recovering the exact original payload, including the TestIO file location. It subsequently identified the requested test and assertion and scored 10.0. That run used 101,923 cumulative API tokens, compared with 53,433 for baseline and 29,340 for pruner in the same question/repetition. This trace establishes actual recovery use and its resource cost; causal attribution of a quality improvement would require a controlled replay.

A fixed component demonstration uses the 217-line albavision.py source file and a query about token transformation and adjacent-hour timestamps. The released model reduces 1,687 code tokens to 169, retaining the transformation function and the current/previous-hour call. The observed request completes in approximately two seconds. A separate real-code service smoke measured peak allocated GPU memory of approximately 2.88 GB.

The demo then retrieves original lines 191–215 by observation ID and verifies exact string equality with the saved source range. This is a scripted component demonstration: the script chooses the recovery range. Autonomous use of recovery is measured separately in the formal trajectories. Unit tests additionally cover mixed CRLF/LF endings, Unicode, overlapping reads, unknown IDs, invalid ranges, and the per-read line limit.

## 5. Debug diary and implementation changes

An initial combined WSL GPU installation triggered a large dependency download. Inspecting the machine revealed an existing CUDA-capable PyTorch environment. Reusing it through an isolated environment completed GPU setup without another full installation. Large downloads are routed only after checking their size and the available network paths.

The original runner unconditionally enabled a Claude-specific HTTP patch, which failed on the OpenAI-compatible route before useful execution. Disabling that patch restored the supported client path. Local service calls explicitly bypass environment proxy settings. External TLS connection failures were traced to the explicit proxy configuration; the API client was changed to bypass that setting. A per-request ledger preserves completed usage and transport failures.

The initial budget guard reserved request bounds even when TLS connection establishment failed. Such ConnectError events occur before request transmission; their provisional reservations were released while retaining the original ledger rows. Uncertain failures after transmission retain conservative reservations. This distinction prevents known connection failures from consuming the entire trial ceiling while keeping ambiguous outcomes accounted for.

The authors' usage aggregation added both cumulative counters and their individual components. An elif correction prevents this duplication; provider per-request usage is authoritative here. A missing optional usage_id also required a default. The saved configuration print was made credential-safe. These compatibility and accounting repairs apply across the affected conditions; the substantive intervention remains the recoverable observation interface.

During formal evaluation, recovery/question 14/repeat 0 reached the 30-step limit and exposed an additional fallback-route issue: the direct OpenAI client passed the SDK's openai/ model prefix to the provider and omitted the task session header. That attempt remains an execution failure in the primary inventory. After the first six scheduled attempts, the fallback was corrected to use the canonical model name and existing task headers. The prior and amended runtime sources are archived, and a recording-client test verifies both fields. The model, prompts, limits, threshold and judge are unchanged. This mid-run infrastructure amendment and its retained failure limit a clean causal interpretation of the pooled comparison.

An initial FP32 model with fixed 8,192-position padding incurred heavy memory pressure and exceeded the service timeout. Explicit stored precision, dynamic single-example length, and omission of unused attention matrices reduced the observed inference footprint. The numerical checks and exact tested environment document the resulting implementation difference.

A second pipeline defect appeared in baseline/question 33/repeat 1: the trajectory contains a complete FinishAction.message, while the saved answer is empty. The authors' extractor checks the action name; this SDK action has a null name and identifies itself through kind=FinishAction. Its eight-action trajectory also falls below the fallback trigger. The primary inventory retains this export failure and its resource use. Accordingly, completion rates measure exported-answer availability, and the preserved trace distinguishes the extraction defect from answer-generation quality. The frozen runtime and original score remain unchanged for the scheduled comparison.

Pruner/question 11/repeat 2 reached the iteration cap and invoked the corrected fallback route successfully. The provider reported all 4,096 completion tokens as reasoning, leaving no final answer. This bounded-generation failure remains in the primary inventory. Provider usage includes the unsuccessful fallback's tokens and cost.

## 6. Conclusions and limitations

{{CONCLUSIONS}}

The reusable XJ13 contribution is a small task-scoped observation store with stable IDs, exact line recovery, and read accounting. It can accept serialized JSON tool output through the same string interface. XJ13-specific lookup, conditional, and aggregation benchmarks require their own evaluation; this report measures the coding-agent setting.

For future users, record actual pruning activation, cache-aware provider usage, and failures alongside answer scores. Pin repository and question revisions, validate model memory on representative tool outputs, and separate development troubleshooting from scheduled evaluation. These controls make the observed trade-offs interpretable even when the accessible LLM differs from the publication.

## References and artifact map

[1] SWE-Pruner: Self-Adaptive Context Pruning for Coding Agents. arXiv:2601.16746, 2026. https://arxiv.org/abs/2601.16746

[2] Authors' implementation. https://github.com/Ayanami1314/swe-pruner (pinned revision above).

[3] Streamlink source repository. https://github.com/streamlink/streamlink (pinned revision above).

Code: README.md, prepare_upstream.py, run_task.py, run_formal.py, observation_store.py, recovery_tool.py. Configuration: configs/task_selection.json and configs/evaluation_protocol.md. Evidence: per-task answers, trajectories, scores, and the API usage ledger. Component validation: validate_pruner.py and demo.py. Recording guidance: demo_script_zh.md. AI assistance contributed implementation, debugging, experiment operation, and drafting; measured results derive from the saved executions and require the student's review.
