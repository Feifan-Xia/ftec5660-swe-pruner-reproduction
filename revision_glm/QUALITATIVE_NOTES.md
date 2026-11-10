# Evidence notes for final interpretation

## Judge sensitivity: q41 baseline repetition 0

The fixed-route primary GPT-5 score was 4.6 (correctness 3, completeness 3, relevance 4, clarity 8, reasoning 5). The reference asks where TestIO validates the dirty flag: `tests/test_cache.py`, `TestIO.test_load_data` at line 413, with `assert cache._dirty is dirty` at line 420 in the pinned source.

The candidate leads with the production `Cache` class and explains `_dirty`, `_load` and `_prune`. It later explicitly names `TestIO.test_load_data` and the two expiration cases, but omits the exact assertion and emphasizes implementation rather than the requested test location. The score therefore measures reference-focused answer fit as well as factual mechanism understanding. Preserve the primary score. A low rubric score alone is insufficient evidence that every factual statement is wrong.

Use this as a code-grounded scoring-sensitivity example if relevant after the full result set. Avoid changing the primary judge or selectively replacing scores in response to this example.

## Goal-shift mechanism experiment

All eight preselected fixtures were retained. Seven lost the target literal under the fixed import-inspection pruning goal; one retained it. Over three executions each, full observations and recoverable observations each achieved 24/24 exact matches; pruned-only observations achieved 3/24. The recoverable condition made 29 successful range reads and returned 28,315 characters. Its cumulative tokens were 55,617 versus 24,082 for full observations and 20,655 for pruned-only observations.

Interpretation: exact recovery restored missing information in the stored-observation setting, while extra requests and tool context increased total model work. The task explicitly changes investigation goals and limits evidence to the saved observation; ordinary SWE-QA agents can also reread repository files. Use the autonomous formal experiment to assess uptake and end-to-end usefulness in that broader setting.
