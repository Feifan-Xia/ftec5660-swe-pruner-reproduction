# SWE-Pruner: Reproduction and Exact Recovery

Xia Feifan · 1155204948

FTEC5660 Individual Reproducibility Project · 11 November 2026

## Abstract

We run the released SWE-Pruner/OpenHands pipeline and checkpoint with GLM-4.6 on eight fixed Streamlink questions, three conditions and three executions: 72 completed cells. Full, pruned and recoverable observations score 8.63, 9.27 and 9.13, using 112.8K, 131.0K and 139.8K cumulative tokens. Pruning increases tokens by 16.1%, contrasting with the paper's 54.4% decrease. Activation, long outputs and subsequent investigation explain the local discrepancy. Our isolated modification adds task-scoped original-observation storage and bounded exact range recovery. A separate 72-cell goal-shift experiment improves exact matches from 3/24 after pruning to 24/24 with recovery, with additional context cost. Evidence accessibility is demonstrated; retrieval decisions determine the end-to-end trade-off.

## 1. Reproduction target

Coding agents repeatedly search and read repositories. A long tool response can remain in conversation history and be transmitted again in subsequent requests. SWE-Pruner filters such responses using an agent-supplied focus question and a released 0.6B neural skimmer [1,2]. This project, item 26 on the instructor's list, runs the authors' OpenHands/SWE-QA pipeline on Streamlink and examines its quality/resource trade-off.

The numerical target is the GLM-4.6 Streamlink row in Table 2:

| Published condition | Mean score / 10 | Mean rounds | Tokens per question |
| --- | --- | --- | --- |
| GLM-4.6, full observations | 8.56 | 18.2 | 318,200 |
| GLM-4.6 + SWE-Pruner | 8.56 | 25.0 | 145,100 |

The reported 54.4% token reduction accompanies unchanged average quality and more rounds. Evaluating this claim therefore requires measuring both context length and interaction count. The report asks whether the same trade-off appears locally, where discrepancies arise, and what changes when the agent can recover exact original observation lines.

The main experiment uses the matching GLM-4.6 model identifier, released skimmer weights and author pipeline on eight predefined questions, with three executions per condition. A separate fixed-context experiment tests recovery after a change in investigation goal. The main experiment measures autonomous task behavior; the second isolates access to evidence removed from a saved observation.

<!-- page -->

## 2. Controlled experimental design

### 2.1 Data and common configuration

The released Streamlink file contains 48 questions. The project originally shuffled indices with seed 5660, reserving 43, 26 and 17 for development and selecting 41, 14, 30, 8, 11, 46, 33 and 29 for evaluation. All indices are zero-based. The sample covers Cache tests, Kaltura, CDP, OpenSSL derivation and DASH serialization; four questions concern CDP. The subset predates the GLM revision; earlier model runs remain development records.

| Control | Configuration and comparability |
| --- | --- |
| Source and data | SWE-Pruner 96171b5; Streamlink ab1f365; recorded question SHA-256 |
| Agent route | OpenRouter z-ai/glm-4.6; Z.AI only; provider fallback disabled |
| Decoding | Temperature 0; top_p 1; 16,384-token output capacity |
| Pruning and rounds | Threshold 0.5 and maximum 250 rounds, matching Appendix D.1 |
| Local time guards | 1,800 seconds/question; 600-second local pruning wait |
| Independent judge | OpenAI GPT-5; exact released five-dimension rubric; low reasoning effort; 4,096 output tokens |
| Environment | WSL Ubuntu 22.04, Python 3.12, OpenHands SDK 1.1.0; Windows GPU service |
| Evidence boundary | Clean repository mounted read-only at /workspace; references remain outside the agent shell |

Initial logs exposed automatic switching between providers with different advertised quantization formats. The definitive study fixes Z.AI, whose endpoint advertises FP4; the paper does not identify its corresponding deployment precision. Matching the model identifier reduces one source of variation while leaving serving implementation as a limitation [3]. The authors' judge comments name GPT-5, whereas executable code selects a deployment through environment variables. This study preserves the exact prompt and records the OpenRouter judge adaptation.

### 2.2 Schedule and failure policy

The three conditions are full observations, SWE-Pruner, and SWE-Pruner with exact recovery. The authors' optional `context_focus_question` triggers pruning; an empty value returns full output. We preserve this autonomous choice and measure actual activation. Questions and shared parameters are identical. Condition order rotates within each question/repetition; three question blocks run concurrently. Three executions measure run-to-run variation; provider seeds are unspecified. First attempts are retained. Missing answers, process failures and pruning-service failures permit one identified recovery attempt. Judge scores never trigger agent reruns; judge transport/schema failures have separate bounded retries.

<!-- page -->

## 3. The scoped modification

### 3.1 Recoverable tool observations

Pruning responds to the current focus question. A later investigation step may require a field, boundary condition or type definition that was previously irrelevant. Retaining the captured original observation provides another way to retrieve such evidence, particularly when the original tool is slow, remote or difficult to repeat.

The primary modification is **task-scoped lossless observation recovery**. A store retains each captured Bash response. The agent receives the authors' pruned result plus an observation ID and line count, and can call `expand(observation_id, start, end)`. Ranges are inclusive, one-based and limited to 200 observation lines per call. Returned characters, repeated lines and expansion actions are logged.

| Step | Interface behavior | Evidence |
| --- | --- | --- |
| Capture | Store original text under a content ID | ID matches SHA-256 prefix |
| Prune | Released weights, focus question, threshold 0.5 | Raw service response and retained tokens |
| Expose handle | Append ID and observation line count | Complete conversation trace |
| Expand | Return original range without rerunning the tool | Exact stored-text slice |
| Account | Record range, characters and repeated lines | Store manifest and API usage |

Exactness is defined over the captured tool text. The original Bash executor strips outer stdout whitespace, so the contract starts after that capture step. File line numbers printed by `cat -n` and observation-range coordinates are separate.

### 3.2 Hypothesis and expected costs

Recovery may repair missing evidence and reduce repeated searches. It also adds storage, an index in the prompt, a tool schema and potentially more model turns. The autonomous comparison measures uptake and the resulting quality/resource trade-off. The fixed-context experiment directly tests access to missing evidence after a goal change.

A pre-run integration check pruned a 6,959-token response to 693 tokens and recovered original observation lines 1–100, matching all 4,434 characters exactly. This establishes the interface contract; downstream experiments assess its task-level consequences.

The standard-library-only `observation_store.py` is separate from the OpenHands binding in `recovery_tool.py`. XJ13 can reuse the same contract to retain raw observations, expose relevant views, recover ranges by ID and measure actual reads. The current store lifetime is one task.

<!-- page -->

## 4. Main reproduction results

All 72 planned cells are resolved and independently scored, 24 per condition. Means use the same eight questions and three executions; SD is the sample deviation of the three whole-subset means. Author rounds count agent/user-source events using stats.py; API requests are shown separately.

| Condition | Answers | Score ± SD | Tokens K ± SD | Author rounds | API calls |
| --- | --- | --- | --- | --- | --- |
| Full observations | 24/24 | 8.63 ± 0.10 | 112.8 ± 5.0 | 13.5 | 10.8 |
| SWE-Pruner | 24/24 | 9.27 ± 0.09 | 131.0 ± 30.6 | 15.1 | 9.8 |
| + Exact recovery | 24/24 | 9.13 ± 0.25 | 139.8 ± 23.4 | 14.4 | 11.6 |

Relative to full observations, pruning tokens increased by 16.1%, with a +0.63 score change. Relative to pruning, recovery tokens increased by 6.8%, with a -0.13 score change.

![Figure 1. Means and sample standard deviations over three executions per question: cumulative API tokens and GPT-5 rubric score.](question_results.png)

| Paired comparison | Token difference K [95% CI] | Score difference [95% CI] |
| --- | --- | --- |
| Pruner − full | +18.2 [-22.9, 66.7] | +0.63 [0.04, 1.52] |
| Recovery − pruner | +8.8 [1.8, 18.8] | -0.13 [-0.52, 0.13] |

Intervals resample eight question clusters 10,000 times with seed 5660, retaining each question’s three executions together. These paired intervals describe subset differences; figure error bars describe within-question execution variation.

<!-- page -->

## 5. Explaining the observations

Locally, pruning tokens increased by 16.1%, compared with the paper’s 54.4% decrease; the local score difference is +0.63, versus 0.00 in the paper. The authors’ pairwise filtering rule retains 24 pairs with all dimensions above one; filtered full/pruner scores are 8.63/9.27. Population, scoring deployment and environment differences require trajectory-level interpretation.

### 5.1 Local compression and cumulative context

Cumulative usage is `C = sum_t (I_t + O_t)`, including cached input and provider-accounted reasoning within output. The skimmer's retained-token fraction measures compression of a particular tool response using its own tokenizer. Total C also depends on request count, subsequent prompt lengths and generation volume. Request-level usage and trajectories separate these layers.

Pruning activates in 10/24 tasks: 16 calls reduce 268,659 source tokens to 63,009, a 76.5% reduction. Recovery activates pruning in 4/24 tasks. Autonomous choices also change repository-reading paths.

We inspect q30 and q11, the largest mean token decrease and increase. For q30, full/pruned means are 249.8K/167.6K. In repetition 1, page.py shrinks from 54,349 source tokens to 13,107; peak input falls from 40,427 to 18,258, with 11/10 API calls. Local compression translates into cumulative savings on this trajectory.

For q11, full/pruned means are 358.2K/520.4K; all three pruning-condition executions omit the focus question. Repetition 3 recursively searches the CDP directory for deserializers and event parsing, repeatedly carrying full results. Peak input reaches 43,299 and total tokens 826,860, versus 15,306 and 305,129 for full observations. This reflects tool selection and investigation paths. A post-hoc influence check omitting q11 gives a −2.4K token difference across the other seven questions. Primary statistics retain all eight; the token interval spans both directions.

![Figure 2. Cached/uncached input and output composition, and provider-reported agent cost for selected formal executions.](resource_breakdown.png)

The score gain concentrates in q41: full/pruned means are 5.00/8.53. The question asks for TestIO.test_load_data; full answers foreground production Cache logic, while pruned answers directly locate the test. The first full answer scores 4.6 despite explaining the dirty mechanism correctly. Original scores remain unchanged. Omitting q41 in a post-hoc influence check changes the score difference from +0.63 to +0.22, illustrating sensitivity to one question and answer granularity.

<!-- page -->

## 6. What changed with exact recovery?

### 6.1 Autonomous behavior and outcomes

Recovery succeeds in 4/24 tasks, with 21 expansion actions and 17 successful reads, returning 62,921 characters and 8 repeated lines. Compared with the preceding display, 16/17 reads expose previously absent nonblank lines. Relative to pruning, score changes by -0.13 and tokens increased by 6.8%. Task difficulty and self-selected tool use also affect uptake; the following intervention isolates access to saved evidence.

In q29 repetition 1, the agent reconstructs the entire 1,032-line generator through eight successful reads, with seven overlapping lines. Two 201-line inclusive ranges are rejected and then corrected. Recovery uses 189,803 tokens versus 59,266 for full observations; both score 10. The interface delegates reading decisions to the agent, which can choose full reconstruction. In q30, selected expansions instead expose missing class definitions. These traces illustrate both evidence recovery and the cost of the chosen retrieval policy.

### 6.2 Fixed-context goal-shift test

Eligible pinned plugin files contain 25–180 lines and an uppercase string constant. After sorting filenames, seed 5660 selects eight files. Each observation is pruned for an import-inspection goal; a follow-up asks for the exact selected constant. Full, pruned and recoverable observations are compared over three executions, scored by exact JSON-string equality. Selection precedes model calls, and every selected case remains in the analysis. Each file fits within one 200-line expansion, so this test primarily measures evidence accessibility; the main-study traces additionally show range selection in long observations.

| File | Target retained | Full | Pruned | Recoverable |
| --- | --- | --- | --- | --- |
| nrk.py | True | 3/3 | 3/3 | 3/3 |
| vk.py | False | 3/3 | 0/3 | 3/3 |
| dailymotion.py | False | 3/3 | 0/3 | 3/3 |
| goodgame.py | False | 3/3 | 0/3 | 3/3 |
| sbscokr.py | False | 3/3 | 0/3 | 3/3 |
| zdf_mediathek.py | False | 3/3 | 0/3 | 3/3 |
| huajiao.py | False | 3/3 | 0/3 | 3/3 |
| cnbce.py | False | 3/3 | 0/3 | 3/3 |

Full observations achieve 24/24, pruned observations 3/24, and recoverable observations 24/24. Seven targets were removed; the surviving nrk.py target is answered correctly in all conditions. The recovery condition makes 29 successful range reads, retrieving 28,315 characters and repairing missing-evidence errors in these fixed cases.

The trade-off is substantial: tokens total 24,082 / 20,655 / 55,617 for full / pruned / recoverable observations, costing $0.019846 / $0.022615 / $0.035627. Pruned-only output rises to 6,585 tokens versus 3,373 for full observations; more expensive output makes the smaller-token condition costlier. Recovery mainly increases input: 52,482 versus 20,709, reflecting additional turns and retransmitted context. This supports preserving evidence for later goals. Repository agents can also reread files, so autonomous net utility is assessed separately.

<!-- page -->

## 7. Reproduction blockers and repairs

| Observed problem | Repair and verification |
| --- | --- |
| Completed task exported an empty answer | Recognize FinishAction by type when name is null; regression test passes |
| Long inputs exceeded local GPU memory | Tile SDPA queries while retaining all keys/values and causal masks; numerical and memory checks |
| Large files/concurrent pruning exceeded the wait | Uniform 600-second local wait; retain 1,800-second question guard and explicit failure records |
| API silently switched deployments | Retain route audit; pin Z.AI agents and OpenAI judges; disable provider fallback |
| Judge transport returned non-JSON data | Preserve errors and retry within a bound; retain the same agent answer |
| Reference-answer access boundary | Read-only repository namespace; tests verify host-path and key exclusion |

### 7.1 Local GPU feasibility

The machine has an RTX 5060 Laptop with 8,151 MiB physical memory. Existing CUDA/PyTorch dependencies and released weights were reused. Long development inputs exceeded the original 60-second pruning-service wait; the failure logs are retained. Query tiling bounds the attention work matrix while every query still attends to the complete key/value sequence.

| Input tokens | Reference | Ref./tiled seconds | Ref./tiled GiB | Decision changes |
| --- | --- | --- | --- | --- |
| 2813 | full_sdpa | 1.33/1.18 | 3.34/3.05 | 0 |
| 4096 | full_sdpa | 1.99/2.23 | 5.04/3.50 | 0 |
| 7044 | tiled512 | 5.94/6.50 | 4.57/4.54 | 0 |

These fixed checks preserve token decisions at threshold 0.5. The 7,044-token check compares tile sizes 256 and 512; an excessively slow full-SDPA long-input comparison was stopped and preserved as development evidence. A separate padding sensitivity check changes one token decision on its second short probe. These observations establish feasibility and the tested numerical behavior while retaining finite-precision uncertainty.

First attempts export 24/24/24 complete answers in full/pruner/recovery order; 72 formal attempts are retained and all 72 planned cells are scored. Fixed-route main/mechanism calls report $2.5666. Project accounting, including earlier stages, development and conservative reservations, totals $7.9262 against the approved $12 ceiling. Raw evidence, launch snapshots and cell-level audit accompany the report.

All agent first attempts succeeded. The first judge request for q29/full/repetition 1 encountered RemoteProtocolError and completed on the bounded retry with the same answer. The unsettled request retains a conservative $0.1161475 reservation.

<!-- page -->

## 8. Conclusions and scope

**Reproduction.** The released pipeline executes and compresses long observations. In this eight-question subset, source text processed by the skimmer shrinks 76.5%, while cumulative tokens increase 16.1% and score rises 0.63. The local resource trade-off differs from the paper's aggregate saving; q11's investigation trajectory has the largest influence.

**Modification.** Exact recovery improves goal-shift correctness from 3/24 to 24/24. Autonomous QA instead uses 6.8% more tokens than pruning and changes score by −0.13, with a score interval spanning zero. Traces show both missing-evidence retrieval and full-file reconstruction.

**Next steps.** Broaden question coverage and define retrieval budgets, indexing and stopping policies on development data before freezing evaluation. XJ13 can reuse task-scoped storage and compare structured-record projection and slicing through evidence coverage, repeated reads and total interaction cost.

### 8.1 Interpretation limits

**Sample composition.** Eight of 48 released questions are evaluated, with CDP accounting for half. Long generated code can influence pruning gains. Repetitions and question-cluster bootstrap intervals describe this subset; broader coverage requires a larger experiment.

**Serving and judgment.** Model/provider pins control deployment variation within this comparison. The paper's exact deployment, quantization and judge configuration are incompletely specified. Reference-based rubric scores also depend on answer focus, reference granularity and judge behavior. Raw scores are retained alongside code-grounded case inspection.

**Environment.** The study uses a read-only snapshot, an 8GB GPU and a shared local pruning service. Token comparisons are backed by per-request usage; concurrent wall times include queueing and network effects. The goal-shift test deliberately limits evidence to a saved observation and supports a mechanism-specific conclusion.

### 8.2 Artifact map

`revision_glm/protocol.json` defines the design; `run_study.py` executes the schedule. `results/glm/` contains cell-level results, paired statistics, recovery-trace analysis and audit. `runs/glm/pinned/` retains question inputs, answers, trajectories, raw API responses, usage and exact launch-source snapshots. The modification is in `observation_store.py` and `recovery_tool.py`. README supplies installation, run and verification commands.

AI assistance was used for implementation and report preparation. Experimental values are produced from saved executions and analysis scripts. A narration/demo script is included; recording and publication remain student steps.

### References

[1] SWE-Pruner: Self-Adaptive Context Pruning for Coding Agents. arXiv:2601.16746v1, Table 2 and Appendix D.1. [Paper](https://arxiv.org/html/2601.16746v1)

[2] Released implementation and SWE-QA scoring/statistics scripts, commit 96171b5f3ecaf89745cbeb436c8893b57f3400bd. [Repository](https://github.com/Ayanami1314/swe-pruner/tree/96171b5f3ecaf89745cbeb436c8893b57f3400bd)

[3] OpenRouter Provider Routing: provider.only and allow_fallbacks. [Documentation](https://openrouter.ai/docs/guides/routing/provider-selection)

[4] Released code-pruner checkpoint, revision 863cee3198c715c9df1faa422a3490e0832bb734. [Model](https://huggingface.co/ayanami-kitasan/code-pruner)
