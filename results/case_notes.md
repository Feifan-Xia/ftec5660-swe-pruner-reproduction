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
