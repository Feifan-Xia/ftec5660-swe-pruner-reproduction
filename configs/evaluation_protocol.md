# Proposed formal protocol (budget approval pending)

## Fixed scope

Use the first eight indices in `task_selection.json`: 41, 14, 30, 8, 11, 46, 33, 29.
Run all three conditions three times: 8 questions × 3 conditions × 3 repeats = 72 task attempts.
The development questions (43, 26, 17) are disjoint. Selection does not depend on observed answer quality.
The final sample count is subject to the explicit budget decision; record any change before formal execution.

Use the same DeepSeek V4.1 Flash model, 30-step limit, 600-second task limit, code revision, and repository snapshot for every condition. Retain the authors' optional context-focus mechanism. Record whether pruning actually activated; this is essential to interpreting any effect. Recovery adds an exact observation store and range expansion without changing the pruning threshold or model.

## Order and failures

Rotate condition order by question and repeat to distribute provider/network drift. Execute serially to avoid repository and GPU contention. Save every formal attempt, including transport failures, timeouts, and missing answers. Formal repeat indices mean distinct scheduled trials; do not replace poor outcomes with successful retries. If infrastructure recovery requires a rerun, assign a separate attempt identifier and keep the original primary record.

## Analysis

Primary outcomes: completion rate, per-task API input/output tokens, wall time, official five-dimension answer score for completed answers, observed pruning activations, and expansion calls. Include all scheduled attempts in completion and resource summaries. Report missing answer scores explicitly; also provide a conservative failure-assigned score of zero as a sensitivity analysis. Preserve the authors' score-filtered results as secondary and label their denominator.

Report condition means and spread over the three repeats. For paired differences, first average repetitions within each question, then compare conditions across the eight question pairs; a question-cluster bootstrap may describe uncertainty but cannot establish generalization from this small subset. Avoid treating 24 runs as 24 independent questions.

The current judge uses the same model family as the agent; label this limitation. The same official rubric and judge settings apply to all conditions. References remain inaccessible to the answering agent. Compare with published Streamlink results only as contextual reference because the model, sample, and runtime differ.

## Isolated modification and XJ13 transfer

The recovery condition changes the availability of original observation lines. Test exact reconstruction and record repeated reads. Separate scripted component demonstrations from autonomous agent recovery use. XJ13 reuse consists of the task-scoped observation store and explicit expansion interface; XJ13's own task benchmark remains a future evaluation.
