# Evidence-linked case notes

## Question 41, repetition 0: correct localization with no pruning activation

The official question asks where `TestIO` determines the dirty flag after loading cached data. Its reference identifies `tests/test_cache.py`, `TestIO.test_load_data`, and the assertion `cache._dirty is dirty`.

The baseline answer identifies that method and assertion, explains the two parameterized expiry cases, and links the dirty property to `_cache != _cache_orig`. This matches the central location in the supplied reference. The same-model official-rubric judge assigned all three conditions a mean score of 10.0.

Provider-recorded cumulative tokens were 36,663 (baseline), 46,492 (pruner), and 36,787 (recovery). All three trajectories contain zero pruned observations and zero expansion calls. This case supports successful repository question answering, while offering no instance-level evidence that compression caused the token differences. Tool availability and divergent action sequences remain part of the observed condition behavior.

Evidence: `runs/formal/{baseline,pruner,recovery}/q41_r0`, the corresponding per-session API ledger rows, and official question index 41. This inspection is AI-assisted and is separate from an independent human evaluation.

## Question 14, recovery, repetition 0: preserved infrastructure failure

At the 30-step cap, the direct fallback client sent the SDK-only model prefix to the proxy. The rejected request led to the saved answer `Unable to generate answer based on conversation history.` The judge assigned 1 in each dimension. The primary completion inventory treats it as a failure, despite the authors' runner printing a successful non-empty output count.

The canonical model name and task session headers were repaired for subsequent scheduled tasks. The first six tasks retain runtime V1, and the remaining tasks use V2; exact code snapshots and the amendment are saved. This failure remains in completion/resource summaries and in the failure-zero score sensitivity analysis. No successful replacement overwrites it.

Evidence: `runs/formal/recovery/q14_r0/console.log`, its saved answer and score, `runs/formal/runtime_manifest_v1.json`, and `runs/formal/runtime_manifest.json`.

## Question 41, repetition 1: autonomous recovery after an over-pruned search result

The recovery agent first requested a focused repository search. The original 29-line output contained the working directory, a directory listing, and `./tests/test_cache.py:331:class TestIO:`. Pruning reduced 851 source tokens to 6 tokens, yielding only `(filtered 29 lines)`. The next agent action invoked `expand` for saved observation `obs_cbd1da5a3453bf18`, lines 1–29.

The returned 1,570-character payload exactly equals the original output after removing the standard `Raw Output: \n` tool wrapper. The saved read manifest records one read and zero repeated lines. The agent then searched `tests/test_cache.py` and eventually identified `TestIO.test_load_data` and `assert cache._dirty is dirty`, alongside the production cache implementation. The rubric judge assigned 10.0.

This trajectory establishes autonomous use of exact recovery after relevant search information was filtered out. Across the whole task, nine outputs were pruned (5,488 source tokens to 2,252 retained tokens), and the agent consumed 101,923 cumulative API tokens. The corresponding baseline and pruner runs consumed 53,433 and 29,340 tokens and scored 10.0 and 8.8. These independently evolving trajectories illustrate the resource/quality trade-off; attributing the score difference specifically to this one expansion would require a controlled replay.

Evidence: `runs/formal/recovery/q41_r1/observations.json`, trajectory events 3–6 (zero-based), saved answer and score; matching baseline/pruner task directories and provider ledger. Verification compared the recorded strings directly. This is AI-assisted trace inspection.

## Question 33, baseline, repetition 1: final answer lost during export

The saved trajectory contains a 2,839-character `FinishAction.message` identifying `test_dash_stream_url` and the JSON serialization logic. Its action has `name: null` and `kind: FinishAction`. The authors' answer extractor recognizes a finish action through its `name`, so it skips this message. With only eight recorded actions, the 30-action fallback is not triggered, and the answers JSONL contains an empty string. The judge assigns 1 in every dimension.

The primary inventory therefore records an answer-export failure, despite successful generation of a final response inside the trajectory. Its 31,370 cumulative tokens remain in resource summaries. The empty exported answer and its original score are retained; completion rates describe exported-answer availability. The trace documents the pipeline defect separately from model answer quality. A comparison of all then-completed formal trajectories found this as the only saved-answer/FinishAction mismatch. Recheck that comparison after the complete schedule.

Evidence: `runs/formal/baseline/q33_r1/answers/openhands/streamlink_answers.jsonl`, the final two trajectory events, `console.log` line containing the eight-action count, and `main.py` finish-action extraction in the archived V2 runtime.
