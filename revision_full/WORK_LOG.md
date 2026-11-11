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

## Earlier state retained for chronology

- User requires subset-first validation. USD 12 remains the approved total; USD 28 is unapproved.
- Author reference archive is local at `runs/author_evidence/swepruner-sweqa-reproduce.zip` (23.9 MB). `DIAGNOSIS.md` now records the decisive findings: Streamlink/Reflex GLM token-column cross-match, exact system/tool prompt equality, source-root layout, 50-step SWE-QA cap, and actual hint coverage 996/996.
- All 22 historical pruned observations replay exactly under the historical kernel. Restoring 8192 padding changes 8 line decisions in 6 observations. Eight author inputs replay with 5 exact pruned texts under BF16.
- A further **verified precision defect**: the released server calls `from_pretrained` without dtype and loads FP32 parameters under the pinned Transformers. Our previous explicit BF16 cast rounded the checkpoint's 15 FP32 tensors. `results/full/published_dtype_check.json` records this. New `serve_fp32.py` preserves the released loading behavior.
- Current BF16, padding-restored, source-root-corrected screen is running for the original fixed eight questions, one repeat × two modes = 16 cells. Runner session **29149**, source `revision_subset/`, outputs `runs/subset/formal`. Complete all 16 and preserve this stage as a diagnostic. It has 12 completed cells at the most recent check, with q11 baseline still active. Never change its GPU service midway.
- GPU BF16 service session **19081**, port 8000. Budget meter session **18947**, port 8879, direct agent route (`AGENT_HTTPS_PROXY=''`), Sakura proxy for the judge. Proxy process **81960**, port 7898. The first new-stage proxy agent attempts incurred three retained transport reserves; after restoring direct agent networking, subset calls have no transport errors so far.
- `runs/full/formal` contains two completed baseline development runs (q17/q43) from the abandoned three-question setup. Its runner was stopped after both completed; preserve them and their charges. All new-stage fees share `runs/full/formal_usage.jsonl` and `budget_authorization.json`.
- The next precision-only correction is prepared under `revision_precision/` but **not frozen or launched**. It references unchanged `revision_subset/runtime`, uses the same fixed eight questions, source-root layout, 50-step cap, and requires FP32 health. First finish the BF16 screen; stop only its owned GPU server, start `revision_full/serve_fp32.py`, replay the same eight author observations with `replay_author_pruning.py --variant fp32`, verify memory and line-level agreement, then freeze and run the corrected paired subset. Use up to 8 workers for speed if the budget reservation headroom allows.
- Analyze complete screens with `revision_subset/analyze.py --partial` then `effects.py --repeats 1`; for precision use corresponding scripts. The analyzers deliberately keep the planned three-repeat denominator separate from the first-repeat screen.
- `revision_full/status.py --study subset` shows current cell/budget state. Current conservative project spending is approximately USD 8.67, with existing USD 12 enforcement.

## Next steps

1. Complete code/history/SDK metric audit and shell failure audit.
2. Replay recorded pruning inputs with original padding; record exact kept-line changes and memory/runtime.
3. Freeze fresh full-population runtime and protocol, with no changes selected by benchmark scores.
4. Launch within approved funds, completing three conditions fairly; retain all first attempts and blockers.
5. Analyze quality, end-to-end token use, activation, fixed-trajectory compression, recovery and cost; compare paper rows in one table.
6. Regenerate and visually inspect Chinese/English reports, reproduce commands and audited release ZIP.

## Current state superseding the earlier snapshot

- The user approved subset-first investigation; the total ceiling remains USD 12. Full 48-question expansion has not been approved at USD 28.
- BF16 corrected-layout/padding screen is complete: 16/16 cells, eight questions, one repeat. Tokens 103,837 → 88,958 (−14.3%); quality 9.55 → 8.90 (−6.8%). Only one task used pruning. This stage remains diagnostic.
- Published default FP32 replay exactly matches 7/8 author pruned texts, compared with BF16 5/8. Source token counts match 8/8. Explicit original fusion arithmetic yields the same texts as FP32 SDPA; the remaining q30 discrepancy is retained.
- Active FP32 server: exec session 82701, port 8000, default query-tiled SDPA. Fixed precision driver session 10112 is finishing its first 16 cells; output `runs/precision/formal`. Sources are frozen and must stay unchanged.
- Baseline system prompt and complete tools also exactly match the author's recorded baseline (`results/full/baseline_contract.json`). Pruner equality was verified earlier. This confirms that current activation differences occur with identical original tool contracts.
- A separate, explicitly labeled required-hint policy intervention is frozen under `revision_hint/`, driver session 65008, four workers, eight initial cells. It makes only `PrunerBashAction.context_focus_question` a required nonempty string. AST isolation and schema checks passed. Reuses the measured precision-stage full/optional controls explicitly. This intervention is not labeled as the original optional protocol.
- Current meter remains session 18947, port 8879; all stages use `runs/full/formal_usage.jsonl`. Conservative cumulative spending approximately USD 9.59, including six unresolved request reservations. No reserve was waived.
- Analyze precision with `revision_precision/analyze.py --partial` and `revision_precision/effects.py --repeats 1`. Analyze required-hint with `revision_hint/analyze.py --partial`; once all eight cells are complete use `revision_full/compare_subset.py --repeats 1`.
- Frozen precision protocol has a stale prose phrase “48 paired question clusters” inherited from the expansion plan. The machine-readable indices/population and implemented bootstrap use eight clusters. Preserve the frozen source and disclose this clerical erratum in the report; no data or analysis changes.
- Subsequent repetitions/expansion depend on the complete fixed-subset evidence and remaining budget. Do not choose questions or retry runs based on score.

### Continued subset validation

- Precision first repetition complete 16/16: full 119857.5 tokens / 9.15 score; optional pruner 86617.25 / 9.00. Relative tokens −27.733%, quality −1.639%. Token bootstrap CI [−41.687%, +14.039%], quality [−4.507%, +1.309%]. Activation 1/8. `results/precision/effects_r1.json` preserves this screen.
- Same immutable precision configuration now completing all three repetitions: driver session **47997**, four workers, `--repeats 3`; previously completed cells are reused. First driver 10112 finished normally.
- Required-hint first screen still active, session **65008**. GPU requests are serialized and long CDP reads take longer; per-task time cap stays 1800 seconds. Complete all eight before analysis or subsequent repeats.
- A pre-reserved standalone Novita/BF16 probe on development indices 43/26/17 finished 0/3 hint activation, cost USD 0.00445126. Its temporary USD 0.35 reservation was released and actual cost added to `prior_stage_conservative_usd`; meter limit reduced by the same actual amount. Unified meter ledger excludes these three requests; `runs/full/diagnostics/novita/` and `external_novita_probe_cost_usd` provide the separate receipt. All other new calls remain in the meter ledger.
- Offline Azure transport reconstruction (`capture_azure_contract.py`) confirms identical author schema, optional hint, resolved temperature 0/top_p 1. No paid call. No source-level schema conversion explains the activation gap. First-user text matches 16/16 original author prompts.
- Current cumulative conservative accounting approximately USD 10.07 including eight unresolved reservations. Keep total USD 12. Do not launch full 48-question experiment or assume USD 28 approval.
