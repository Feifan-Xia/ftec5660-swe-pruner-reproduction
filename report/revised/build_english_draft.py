"""Render an English evidence draft from the completed fixed-subset analysis."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
e=json.loads((ROOT/'results/full/manuscript_evidence.json').read_text(encoding='utf-8'))
assert e['groups']['optional_recovery']['n']==24
def interval(comparison,metric):return ', '.join(f'{x:+.1f}%' for x in e['comparisons'][comparison][metric]['ci95_percent'])
text=f'''# SWE-Pruner Reproduction and Bounded Observation Recovery

Xia Feifan · 1155204948

FTEC5660 Individual Reproducibility Project · November 2026

Completed subset evidence draft · Full-population extension pending

## Abstract

We reproduce SWE-Pruner's repository question-answering experiment using the released OpenHands/SWE-QA implementation, targeting the Streamlink and GLM-4.6 rows of Table 2. After correcting the workspace, step limit, padding and parameter-loading precision, eight fixed questions with three repetitions per condition show 17.6% lower cumulative API tokens and a 1.3% increase in mean answer quality. All three repetitions reduce tokens, but the question-cluster interval includes zero and only 25.0% of pruning tasks activate the skimmer. The authors' released executions on the identical eight questions reduce tokens by 49.9%, establishing a substantial remaining gap. We add task-local storage of captured tool output and exact recovery of bounded line ranges. Under the original optional-hint protocol, recovery increases mean quality by 1.4% at an 11.3% token overhead; the quality interval includes zero. A controlled evidence-retrieval experiment increases exact-match success from 12.5% to 100.0% at a 196.4% token overhead. Artifact audits, matched policy diagnostics and complete failed-attempt records explain the observed tradeoffs and delimit the reproduction claim.

## 1. Introduction

Coding agents repeatedly read source files and include earlier observations in subsequent model requests. SWE-Pruner uses a 0.6B neural skimmer to retain lines relevant to the agent's current focus question before a Bash observation enters the conversation [1]. Its reported benefit combines reduced context with preserved task performance. An end-to-end reproduction must therefore measure the entire interaction path: a shorter observation can save future input, while omitted details can also cause additional searches and rereads.

Our implementation target is the authors' `downstream_eval/multi_turn/sweqa` pipeline at commit 96171b5 [2]. OpenHands supplies the agent loop and tools; SWE-QA supplies repository questions, reference answers and a five-dimensional judging rubric; SWE-Pruner filters tool outputs. The numerical target is the full-observation versus SWE-Pruner comparison for Streamlink with GLM-4.6 in Table 2. Other reported tasks, including SWE-Bench Verified, fall outside this experiment's numerical scope.

The completed fixed subset gives 136.4K → 112.3K tokens per task and quality 9.00 → 9.12. This recovers the direction of token reduction after the earlier local configuration had increased tokens by 16.1%. The authors' own records for the same eight questions give 190.2K → 95.3K, a 49.9% reduction. Their executions and our reruns are distinct sources. The shared questions control task selection, while model serving, execution history and repetition count remain different.

Our scoped modification stores exact captured observations outside the active context and exposes `expand(observation_id, start, end)`, returning at most 200 lines per call. In the original protocol, its 1.4% mean quality increase costs 11.3% additional tokens. Twelve successful reads recover previously unseen nonblank text in three tasks. A controlled follow-up requiring a previously omitted constant verifies exact retrieval independently of autonomous search. Together, these experiments distinguish observation-level functionality, average task outcomes and the costs of additional interaction.

## 2. Method and Modification

### 2.1 Released pruning behavior

The agent supplies a Bash command and an optional `context_focus_question`. A nonempty question invokes the skimmer; an omitted question returns the full captured output. The released tool description permits blank hints for small important outputs and recommends unfiltered `sed` reads for details. Consequently, activation is part of the observed behavior rather than a guaranteed property of selecting the pruning condition.

The skimmer processes chunks padded to 8192 positions, merges overlapping token scores, maps them to characters and averages covered character scores by line. Lines meeting the 0.5 threshold are retained. The implementation also preserves a one-line gap between retained lines and inserts deletion markers [2,3]. We preserve this logic and the released checkpoint. Model parameters are loaded in FP32; the published forward pass uses FP16 autocast and converts logits to FP32. Query-axis SDPA tiles of 256 retain the complete key/value context and permit execution on the local 8GB GPU.

Cumulative API tokens are C = Σₜ(Iₜ + Oₜ), including cached input and reasoning output counted by the provider. Source compression is 1 − Σ kept / Σ raw using the skimmer tokenizer. These measurements have different denominators: cumulative API usage includes repeated history and path changes, while compression describes only observations actually sent to the skimmer.

### 2.2 Task-local exact recovery

`observation_store.py` stores the complete text captured by the Bash executor, keyed by a content hash. `recovery_tool.py` adds the identifier and original line count to the observation and registers an expansion tool. Inclusive, one-based ranges address positions in the saved observation, with a 200-line bound. The store preserves line endings and records returned characters and overlapping reads. Invalid identifiers, out-of-range requests and oversized ranges return explicit errors.

The stored boundary is captured stdout after the original executor's processing. Source-file line numbers printed by `cat -n` can differ from positions within that captured observation. Each task runs in a separate process, giving the store a task-scoped lifecycle. The standard-library storage module is reusable independently of OpenHands, including in XJ13. Additional metadata, expansion turns and returned text contribute to the measured API cost.

### 2.3 Activation-policy diagnostic

All 996 recorded Bash actions in the authors' Streamlink pruning trajectories contain a focus question. Our corrected original protocol activates pruning in six of 24 tasks. On three separate development questions, default, enabled and disabled reasoning produce nine first actions without hints. Three Novita/BF16 first-action probes also omit the hint. These probes preserve the public input contract and stop before executing shell commands.

A separate diagnostic makes the hint a required nonempty string. Its matched full-output control uses the identical required-hint schema while returning all captured text. Comparing that control with actual pruning isolates filtering more closely than comparing different tool descriptions. A third arm adds recovery. All three arms complete the same eight questions once. The original optional-hint protocol remains the main reproduction and modification setting.

## 3. Artifact and Implementation Audits

### 3.1 Published values and author-run records

The authors' README links an archive containing answers, scores, trajectories and settings. Question identities match the respective Streamlink and Reflex files exactly, with 48 questions per repository and no cross-repository overlap. Recomputing input plus output tokens reveals that the GLM token aggregates cross-match the other repository's Table 2 cells, while score and round aggregates retain their own repository correspondence.

| Repository and source | Full tokens K | Pruner tokens K | Change | Full / pruner quality |
|---|---|---|---|---|
| Streamlink, paper Table 2 | 318.2 | 145.1 | −54.4% | 8.56 / 8.56 |
| Streamlink, author records | 142.3 | 101.2 | −28.9% | 8.56 / 8.56 |
| Reflex, paper Table 2 | 142.3 | 101.2 | −28.9% | 8.37 / 8.23 |
| Reflex, author records | 318.2 | 145.1 | −54.4% | 8.37 / 8.23 |

Table 1. Published values and recomputed author-run aggregates. K denotes 1000 tokens. The evidence establishes the correspondence discrepancy; the archive does not establish how it entered the paper.

All 48 Streamlink baseline `token_cost` fields differ from their corresponding input-plus-output fields, so we use the latter and retain both. Original provider receipts are unavailable. The released scoring script excludes paired questions having any dimension scored one; its overall Streamlink 8.56/8.56 uses 43 pairs. On the identical eight questions, unfiltered author scores are 8.25/8.60, while the filtered seven-question means are 9.03/8.40. Our main analysis retains every planned task and makes these denominator differences explicit.

### 3.2 Configuration and numerical alignment

Author trajectories specify a 50-step limit and a shared root containing `swe-repos/conan`, `reflex` and `streamlink`. We restore this layout and the pinned source commits, replacing the earlier Streamlink-internal directory and 250-step limit. Evaluation answers and credentials are outside the read-only tool sandbox. Additional helper files visible in the authors' trajectories were not released and remain an environment difference.

Restoring masked right padding changes eight retained-line decisions across six of 22 historical observations. Loading the checkpoint with the published default preserves 15 FP32 tensors previously rounded by an explicit BF16 cast. On the first substantial author observation for each fixed question, exact output matches improve from 5/8 to 7/8; source token counts match for all eight. The residual q30 output retains 920 tokens locally versus 982 in the author record. An additional replay of the original fused-attention arithmetic yields the same text as the current FP32-loading configuration. Peak allocated GPU memory is approximately 6.5 GiB.

System prompts, complete tool schemas and the 16 initial user prompts for the two original conditions match the author records. A local fake-response capture of the published Azure SDK path also preserves optional hints, temperature zero and top_p one. The original model was served as `azure/glm-4.6` through a ByteDance gateway; our accessible route is GLM-4.6 through OpenRouter/Z.AI with fallback disabled [4]. The original service internals, hardware kernels and actual downloaded checkpoint revision remain incompletely specified.

### 3.3 Usage and terminal-summary repairs

An independent request ledger validates cumulative input and output. Replaying the released runner's simultaneous accumulation of SDK totals and per-call usages gives exactly twice the independent usage in 72 historical tasks. Mutually exclusive accounting branches correct this defect. The public SWE-QA code postdates the paper, so the relationship between that code path and published accounting is uncertain. A uniform factor alone preserves relative token changes.

At the 50-step limit, the released terminal-summary serializer reads inherited `observation.content`, which is an empty list for actual Bash observations. Normal tool interaction sees the real result, but terminal synthesis receives `Observation: []`. The local function is AST-identical to the released one. The repair reads the agent-visible `to_llm_content`, preserving filtered visibility and recovery metadata.

Two affected trajectories receive terminal-only replays on exactly the same completed prefixes. Their first 49 tool displays match saved wire messages character for character; the final observation comes from the same trajectory. Full q11 quality changes from 7.0 to 8.0 (+14.3%), and required-hint q11 from 8.0 to 8.8 (+10.0%). Whole-task tokens increase 2.4% and 1.9%. Original and repaired answers remain separate; repaired metrics subtract the old terminal call and add the new one. These are fixed-prefix branch replays. New recovery executions use the repaired serializer, although none reaches that fallback. The original terminal temperature is 0.3; normal agent requests use zero.

## 4. Experimental Setup

The fixed zero-based indices are 41, 14, 30, 8, 11, 46, 33 and 29, selected before the initial model runs. Full, original optional-hint pruning and optional-hint recovery each complete three executions per question, giving 72 primary cells. The required-hint diagnostic contributes 24 cells and the controlled evidence experiment contributes another 72. All fixed questions remain included. The requested 48-question extension is prepared separately and awaits additional budget authorization.

| Component | Shared configuration |
|---|---|
| Agent | GLM-4.6, fixed Z.AI route, provider fallback disabled |
| Judge | GPT-5, fixed OpenAI route, released five-dimensional rubric |
| Generation | temperature 0, top_p 1, maximum output 16,384; terminal summary temperature 0.3 |
| Limits | 50 interaction steps; 1800 seconds per question |
| Skimmer | Released checkpoint, threshold 0.5, 8192-position padding |
| Runtime | Windows / Ubuntu 22.04 WSL; Python 3.12; OpenHands SDK 1.1.0 |
| Numerical stack | PyTorch 2.9.0.dev20250705+cu129; Transformers 4.57.1 |

Table 2. Common configuration. Provider and unreleased-workspace differences are reported in Section 3.

Quality is the mean of correctness, completeness, relevance, clarity and reasoning, each scored 1–10. Relative changes use 100 × (treatment/control − 1). Success rates use percentages and their differences use percentage points. We bootstrap questions as paired clusters, retaining all repetitions, with 10,000 resamples and seed 5660. Three temperature-zero executions measure observed online variability; no independent provider seed is claimed.

Infrastructure, export, pruning-service and missing-usage failures permit one documented retry. Third or fourth attempts in interrupted diagnostics require every preceding attempt to have stopped under budget protection. All earlier attempts remain. Judges resume on the same saved answer after transport or invalid-format failures, accepting the first valid score. One concurrent duplicate judgment was reconciled by request-start order under that existing policy; both responses and costs remain. Subsequent resumes use per-cell locks and exact cell selection.

## 5. Results and Analysis

### 5.1 Reproduction against the paper and identical questions

| Source and condition | Executions | Quality / 10 | Tokens K | Scope |
|---|---|---|---|---|
| Paper Streamlink full | 48 | 8.56 | 318.2 | Table 2 |
| Paper Streamlink pruner | 48 | 8.56 | 145.1 | −54.4% tokens |
| Author records full | 48 | 8.56 | 142.3 | 43 scored pairs |
| Author records pruner | 48 | 8.56 | 101.2 | −28.9% tokens |
| Author records, same eight, full | 8 | 8.25 | 190.2 | One run per question |
| Author records, same eight, pruner | 8 | 8.60 | 95.3 | −49.9% tokens |
| Local original full | 24 | 9.00 | 136.4 | Eight questions × three |
| Local original pruner | 24 | 9.12 | 112.3 | −17.6% tokens |
| Local terminal-repaired full | 24 | 9.04 | 137.0 | One terminal branch replay |
| Local pruner + recovery | 24 | 9.24 | 125.1 | Original optional hints |

Table 3. Unified published, author-run and local comparison. Author records are recalculated reference data, not local runs. Local scores retain all 24 executions; author whole-repository scores use their filtering rule. Pruner has no affected terminal branch and remains unchanged by the serializer repair.

The original-protocol token reductions are 27.7%, 16.0% and 10.4% across the three repetitions, averaging 17.6%. Mean quality increases 1.3%. The token and quality intervals are [{interval('original','total_tokens')}] and [{interval('original','score')}], respectively. Terminal repair yields an 18.0% token reduction and 0.8% quality increase. Eight independent question clusters limit precision even with three repetitions.

On identical questions, author absolute savings are 94.9K tokens per task versus 24.0K locally. Of the 70.9K gap, approximately 76.0% is accounted for by a lower local full baseline and 24.0% by a higher local pruner cost. For q29, author/local full costs are 217.8K/40.7K, while pruner costs are similar at 68.5K/66.3K. This arithmetic identifies the baseline path as an important part of the comparison; it does not isolate a causal effect of serving or sampling.

![Figure 1. Every fixed question and all three complete repetitions. The left panel preserves question-level heterogeneity; the right panel shows consistent mean token direction across repetitions.](figures/precision.png)

### 5.2 Activation and repeated reading

Original optional pruning compresses 199,487 source tokens to 37,030 (81.4%) across six calls in six tasks. Task coverage is 25.0%, versus 100.0% in the author records. In the first local repetition, q11 contributes 95.3% of net savings without activating the skimmer. Full and pruner tool descriptions differ, so investigation strategy as well as online variability can affect paths even when no text is filtered.

| Required-hint diagnostic | Quality | Tokens K | API requests | Pruning coverage |
|---|---|---|---|---|
| Matched full output | 9.33 | 134.1 | 10.13 | 0.0% |
| Pruned output | 9.20 | 177.6 | 20.13 | 100.0% |
| Pruned, terminal repair | 9.30 | 178.9 | 20.13 | 100.0% |
| Pruned + recovery | 9.33 | 156.9 | 15.63 | 100.0% |

Table 4. Eight questions per arm with an identical required-hint schema. This diagnostic is distinct from the original optional-hint reproduction.

Required pruning reduces tokens per API request by 33.3% but increases the number of requests by 98.8%, producing 32.5% more cumulative tokens than its matched full-output control. Source compression is 68.3%. In q33, repeated cat, sed, Python, grep and awk reads of a test file sometimes retain only seven tokens from outputs exceeding one thousand tokens. The agent subsequently tries smaller ranges. Making hints mandatory closes the unfiltered reread path explicitly permitted by the original tool description. This explains a concrete failure mode of the diagnostic policy and why forcing activation alone does not restore the published efficiency.

### 5.3 Recovery benefits and costs

Under original optional hints, recovery changes quality from 9.12 to 9.24 (+1.4%) and tokens from 112.3K to 125.1K (+11.3%). The corresponding intervals are [{interval('optional_recovery','score')}] and [{interval('optional_recovery','total_tokens')}]. Requests increase 6.0%. The observations support a clear token overhead and an uncertain small mean quality benefit.

Three tasks use recovery, giving 12 successful reads and 51,480 returned characters, with two repeated lines. Every successful read matches the original bounded slice and exposes previously unseen nonblank text. Seven additional requests exceed 200 lines and two use invalid ranges. Their error observations, turns and tokens remain included, documenting an interface cost of range selection.

In the required-hint diagnostic, recovery uses 21 successful reads across five tasks. Relative to terminal-repaired pruning, tokens decrease 12.3% and quality increases 0.3%, with broad intervals [{interval('required_recovery_repaired','total_tokens')}] and [{interval('required_recovery_repaired','score')}]. Recovery can alleviate repeated filtering in this diagnostic, while the original protocol already permits unfiltered Bash rereads. Independent trajectories and eight question clusters constrain causal precision.

The controlled experiment uses eight fixed source observations of 25–180 lines, initially filtered for an import-related focus. A subsequent request asks for the earliest eligible uppercase string constant; cases remain included when the constant survives pruning. Three conditions each repeat three times, totaling 72 exact-match trials. Full, pruned and recoverable observations achieve SR 100.0%, 12.5% and 100.0%. Recovery adds 87.5 percentage points over pruning, at 196.4% more tokens than pruning and 131.9% more than full observations. Twenty-nine expansion reads return 30,189 characters. This verifies retrieval under a controlled evidence shift and quantifies its substantial interaction cost.

![Figure 2. Controlled evidence-retrieval results, 24 trials per condition. Exact-match SR and cumulative follow-up API tokens are reported separately.](figures/mechanism.png)

## 6. Limitations and Reproducibility

The complete subset preserves all eight questions, but its breadth remains smaller than the released 48-question population. Question heterogeneity produces wide intervals. Original and local model/judge serving and unreleased helper files differ. Required-hint filtering is an explicit policy intervention. Sequential stages and shared GPU scheduling affect elapsed time, which is retained as an operational record rather than treated as a controlled speed comparison. Five-dimensional LLM scores provide useful answer comparisons, while small score changes require cautious interpretation alongside answer text.

All 72 primary executions have complete answers, scores and transmitted-request usage. Final execution completeness is 100.0%; first-attempt completeness is 81.9% overall, 79.2% for full/pruner and 87.5% for recovery. The diagnostic 24 and mechanism 72 cells are also complete. Network/VPN changes caused simultaneous resets and occasional DNS/SSL failures. Original failures, missing-receipt attempts, replacements and duplicated judge responses remain auditable.

Frozen protocols, source hashes, source commits, per-task question inputs, trajectories, answers, judge responses and request usage form the provenance chain. Scripts generate the reported aggregates and intervals. Conservative project accounting is approximately $9.69 against the approved $12 ceiling; the full-population extension is awaiting a separate budget decision. The student's recording and explanation use the accompanying demo script. AI assistance supported implementation, analysis and manuscript preparation.

## 7. Conclusion

The corrected fixed-subset reproduction recovers a mean token-reduction direction with broadly maintained answer quality: 17.6% fewer tokens and 1.3% higher mean quality across three complete repetitions. The authors' identical-question reduction of 49.9% and complete pruning activation remain substantially different. Baseline paths, hint behavior, numerical alignment and terminal evidence handling each contribute distinct evidence about this gap. Task-local exact recovery provides auditable access to omitted observations, with a 1.4% mean quality increase at 11.3% token overhead under the original protocol and a large exact-retrieval benefit at substantial cost in the controlled experiment. Full-population validation remains the next required stage of the project.

## References

[1] Yuhang Wang, Yuling Shi, Mo Yang, Rongrui Zhang, Shilin He, Heng Lian, Yuting Chen, Siyu Ye, Kai Cai, Xiaodong Gu. SWE-Pruner: Self-Adaptive Context Pruning for Coding Agents. arXiv:2601.16746v1, 2026. [Paper](https://arxiv.org/abs/2601.16746v1)

[2] SWE-Pruner implementation and released SWE-QA artifacts, commit 96171b5f3ecaf89745cbeb436c8893b57f3400bd. [Repository](https://github.com/Ayanami1314/swe-pruner/tree/96171b5f3ecaf89745cbeb436c8893b57f3400bd)

[3] code-pruner checkpoint, revision 863cee3198c715c9df1faa422a3490e0832bb734. [Checkpoint](https://huggingface.co/ayanami-kitasan/code-pruner/tree/863cee3198c715c9df1faa422a3490e0832bb734)

[4] OpenRouter Provider Routing. Accessed November 11, 2026. [Documentation](https://openrouter.ai/docs/guides/routing/provider-selection)
'''
assert all('?' not in line for line in text.splitlines() if line.startswith('#'))
(HERE/'subset_draft_en.md').write_text(text,encoding='utf-8')
print('Built English completed-subset evidence draft; full-population scope remains active.')
