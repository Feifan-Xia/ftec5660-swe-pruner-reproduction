# FTEC5660 full-population reproduction revision

## Active objective

Investigate the discrepancy, repair verified deviations, complete the released Streamlink population under a frozen paper-aligned protocol, then evaluate the recovery modification and rewrite both reports. The historical eight-question study remains intact. The user prioritizes completion over the previous deadline.

## Authorization and pending budget

Approved project ceiling: USD 12. Historical conservative accounting: USD 7.92620608. A concrete request for USD 28 total is pending: 48 questions × 3 repetitions × 3 conditions = 432 new cells, estimated USD 15–16, plus historical spending and diagnostic/retry margin. No spending beyond USD 12 without a reply.

### User steering on 2026-11-11

The user answered the budget request by asking to obtain the expected behavior on a subset before expanding. **USD 28 is not approved.** Keep USD 12. The currently launched three-question block (43, 26, 17; three repeats, full/pruner) now serves as a development diagnostic, not the final full-population experiment. Preserve the frozen source and all outputs. Inspect the authors' newly discovered reference trajectories before deciding further configuration changes or launch scope. Expand only after the fixed-subset comparison has been reviewed against the target behavior.

The public author archive is linked near the end of the SWE-QA README: Google Drive ID `18YPXGHuiqox8zUMt06l9j0nFt_zXMK75`, file `swepruner-sweqa-reproduce.zip`, 23,888,187 bytes, published 2026-03-08. Connector metadata/fetch succeeded; downloading to local disk is in progress. This archive is essential evidence for exact prompts, activation, token accounting and reported-table provenance.

## Verified findings

- Historical 72 cells: all 772 agent requests used GLM-4.6, Z.AI, temperature 0, top_p 1, output cap 16384; one system-prompt hash throughout. Provider reasoning metadata is present (usually short/dynamic).
- Every exported runner token total equals the independent request-ledger sum. The released upstream code has two consecutive accumulation branches; our old compatibility patch makes them mutually exclusive. Whether the *paper* used that exact buggy branch remains unknown. This potential factor affects absolute tokens; a uniform factor cannot reverse the percentage direction.
- Paper Appendix J, PDF page 28, SWE-QA tool descriptions match the released/current tool strings, including optional hints, numbered full-file reads and unfiltered sed recovery.
- All historical agent runs have no tool timeout/error-prefix outputs. Commands that fail with only stderr may still appear as `(No output)` because the authors' executor returns stdout only; inspect this separately.
- Historical experiment population is 8 of 48 questions, with 4 CDP questions. Full-population rerun is required for coverage.
- Old local inference omitted masked right padding. Earlier token-level tests found a threshold disagreement on one probe. The new inference should restore the authors' 8192-position padding while retaining tested memory-bounded attention. Verify line-level outcomes on recorded observations.

## Next steps

1. Complete code/history/SDK metric audit and shell failure audit.
2. Replay recorded pruning inputs with original padding; record exact kept-line changes and memory/runtime.
3. Freeze fresh full-population runtime and protocol, with no changes selected by benchmark scores.
4. Launch within approved funds, completing three conditions fairly; retain all first attempts and blockers.
5. Analyze quality, end-to-end token use, activation, fixed-trajectory compression, recovery and cost; compare paper rows in one table.
6. Regenerate and visually inspect Chinese/English reports, reproduce commands and audited release ZIP.
