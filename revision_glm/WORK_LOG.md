# Revision work log — 2026-11-11

## Current state

- User extended completion to Nov 11 and explicitly approved a $12 project ceiling, completeness first. The goal remains active.
- The definitive experiment is **fixed-provider v2**, commit `a514c2b`, protocol `revision_glm/protocol.json`, output `runs/glm/pinned/formal/`. It runs 8 questions × 3 conditions × 3 repetitions, with GLM-4.6 restricted to Z.AI, GPT-5 restricted to OpenAI, temperature 0, threshold .5, 250 rounds, 1800-second question guard and 600-second local pruning wait. Three parallel question blocks, cyclic condition order.
- The final run was launched around 00:31. Tool session **57099** runs the WSL study. The meter is session **27825**, port **8879**. GPU service is session **35112**, Windows process **80556**, port **8000**. A dedicated isolated SakuraCat US proxy is session **81094**, port **7898**, with private ignored config under `runs/network_glm/`; never package that directory.
- Meter authorization is `runs/glm/pinned/budget_authorization.json`; current meter allowance is $6.756494 within the $12 project total. Prior conservative/development accounting is $5.093506, with a $0.15 margin.
- At about 00:44, 12 primary cells had completed and scored, with no unresolved qualification failures. All pinned requests observed Z.AI/OpenAI as configured. Progress is available through `analyze.py --partial`.
- The separate fixed-provider goal-shift experiment **finished all 72 cells** (session 80614 exited). `results/glm/mechanism.json` is final: full 24/24, pruned 3/24, recoverable 24/24; 29 successful expansions, 28,315 characters; token totals 24,082 / 20,655 / 55,617; costs $0.019846 / $0.0226154 / $0.03562652. Seven of eight preselected fixtures lost their target literal; all cases were retained. This is a controlled saved-observation/goal-shift test, separate from autonomous repository QA.

## Key fixes and provenance

- The prior DeepSeek reports and release package remain historical. Their 23/24 answers per condition are not the revised final experiment.
- `FinishAction.name=None` now exports the actual final message. WSL regression tests pass.
- Every shell command runs in bubblewrap over a clean read-only repository archive at `/workspace`; reference answers, host files and keys are excluded. WSL isolation test passes.
- Long input originally exceeded 8GB physical GPU memory and timed out. `memory_attention.py` tiles SDPA queries, retaining all keys/values and causal/padding masks. CPU mask/GQA/causal tests pass. `runs/glm/attention_validation.json`: exact output match for 2813/4096-token probes versus full SDPA; 7044 tokens with tiles 256/512 also match, about 6.5 seconds / 4.54GiB peak. Original long baseline comparison was stopped after several minutes; the earlier partial output is preserved, and the long numerical reference is explicitly tile-512, not full SDPA.
- `runs/glm/pruner_numerical_validation.json` records one token decision changing at threshold .5 under padding on the second old probe. Disclose this finite-precision limitation.
- Live recovery integration: source 6959 tokens → 693 retained, exact expansion of observation lines 1–100. `runs/glm/integration_check.json`.
- Initial mixed-provider study revealed Venice FP4 / Z.AI FP4 / Novita BF16 routing. It was deliberately stopped and retained at `runs/glm/formal/STOP_REASON.json`; frozen sources from commit `0a0fdee` are archived there. Fixed-provider v2 starts every primary cell fresh. Preserve this development provenance.
- Mixed-route GPT-5 once returned a transport error; v2 records/retries non-JSON transport failures. Primary judge results are never replaced based on score.
- Authors `stats.py` rounds count all agent/user-source events. Record that alongside API request count. Its filtered score uses pairwise common questions and excludes any score dimension equal to one.
- GPT-5 executable source takes a deployment from environment; comments name GPT-5. Our exact released rubric plus OpenRouter GPT-5 low reasoning effort is an explicit serving adaptation.

## Work still required

1. Monitor session 57099 through all 72 cells. Diagnose every failure and finish the frozen schedule under its preserved retry policy. Do not change frozen inference files during the run. A restart reuses finished cells. `resume_study.py` is a transport wrapper if needed; current v2 runner already handles the observed error type.
2. Run final `analyze.py`, `analyze_mechanism.py`, `analyze_recovery.py`, then `audit.py`. Current `audit.py` checks exact launch files, input questions, score provenance, provider pins, token accounting, recovered ranges, 72+72 completeness and budget. Investigate any mismatch rather than suppressing it.
3. Read complete per-question outcomes and inspect predeclared largest token decrease/increase cases, autonomous recovery traces and a scoring-sensitive answer. `QUALITATIVE_NOTES.md` documents q41 baseline r0 (score 4.6): answer explains Cache mechanics and mentions TestIO.test_load_data, but emphasizes the wrong requested location and omits the exact assertion. Keep its judge score; analyze reference-focus sensitivity honestly.
4. Write new Chinese and English reports, max 10 pages each, around the main outcome, paper comparison, mechanisms and modification effects. `REPORT_PLAN.md` is the argument plan. `report/glm/render.py` is a new embedded-font Markdown-to-PDF renderer; `report/glm/figures.py` builds paired question and resource plots from final results. Final prose has NOT been written yet. Use new output directory `report/glm/`; preserve old reports as historical.
5. Update root README, demo narration script and submission checklist with the final matched-model results. `revision_glm/README.md` already documents setup/run/metrics, including environment-key configuration. Generated runtime provenance and small modification files should be easy to review.
6. Improve formatting of new Python code after the study finishes if useful; preserve exact launch snapshot and prove AST equivalence if frozen source formatting changes. Current audit requires exact current bytes, so avoid gratuitous changes or adapt the audit transparently for formatting-only provenance.
7. Render and inspect every final report page. Verify all numbers/claims against final JSON, code and trajectories. Produce a new reviewed artifact bundle, Git history and SHA manifest. Package allowlisted `runs/glm/pinned/` evidence and relevant development files; exclude API keys, CC Switch DB, and all `runs/network_glm/` private proxy config. Include upstream/Streamlink licenses. User will record/publish/submit.
8. Mark the goal complete only after the revised deliverables and checks are done. No grade guarantee.

## Communication and automation notes

No proactive subagents. User prefers concise Chinese, positive connected explanations. They want progress and rigorous results, not repeated budget worry. An extra ad-hoc local generation probe command was automatically rejected with only “blocked by policy”; this was explained to the user. The optional probe was omitted; successful authorized fixed-route study requests subsequently verified routing. No current approval blocker remains.


## 2026-11-11 01:29 progress and release preparation

Fixed-provider primary study remains in session 57099 (meter 27825 / port 8879, GPU 35112 / port 8000). 59/72 resolved at last analysis; all scored and qualified. Remaining q11, q29 and final q33 pruner execution. All current provider requests return 200. Preserve frozen runtime until completion.

Prepared bilingual eight-section templates, renderer, figures and composer in report/glm. Final composer requires reviewed_interpretation.json with zh/en ABSTRACT, CASE_ANALYSIS, JUDGE_ANALYSIS, CONCLUSIONS. Final result analysis must wait for 72 cells. Layout-only previews are ignored under report/glm/layout_preview.

Root README now leads GLM revision. New demo_recovery.py successfully replays saved vk.py prune output (1061 -> 678 tokens), expands original lines 34–38, and verifies exact recovery of API_URL. It runs locally without API/GPU. Chinese demo_script_zh.md rewritten. SUBMISSION_CHECKLIST.md and PROJECT_STATUS.md still need final replacement.

Core tests: 5/5 pass. WSL final-export and shell-isolation tests pass; GPU attention mask/causal test passes separately. Analysis, mechanism/recovery analyzers, audit/package/report scripts formatted for readability; frozen inference files unchanged.

Preliminary audit on 56 primary cells: only incomplete-population errors; source hashes, request providers, score provenance, captured original text/ranges and budget all pass. Added checks for selected pruning failures, raw successful responses and mechanism fixture equality to pinned repository. Final audit must overwrite this preliminary FAIL after complete analysis.

Package manifest fixed to include source_sha256 required by scripts/verify_bundle.py. Final package requires clean committed tracked source and PDFs. It includes all pinned evidence, endpoint metadata snapshot, Git bundle and licenses, excludes private network_glm configuration. Secret scan found no OpenRouter key pattern in revised sources/reports/results.

Qualitative evidence: q30 is strongly token-saving in completed three repeats (baseline mean249778, pruner167607). Pruner r0 reads page.py54349 source tokens ->13107, 10 APIcalls vs baseline11, maxprompt18258 vs40427. Recovery q30r0 performs 4 successful reads, one redundant; exact counts final analyzer. q11 many short commands and zero pruning, long investigation of from_json dependencies. q41 baseline answers correctly discuss Cache._dirty and mention test_load_data later, but lead with production Cache implementation; question explicitly asks location in TestIO. Judge scores4.6/5.0/5.4 vs pruner9.0/8.2/8.4. q33 recoveryr0 score5.6 also shifts focus to production implementation instead of test assertion. Discuss focus/granularity sensitivity and preserve original scores. Final select largest mean token decrease/increase after all questions complete; report post-hoc leave-one-question-out influence diagnostics without changing main population.

Next: complete72 -> analyze.py, analyze_mechanism.py, analyze_recovery.py, audit.py -> inspect final extremes -> reviewed_interpretation.json -> figures.py,compose.py,render both PDFs -> visually inspect every page <=10 -> final docs/results/commits -> package.py -> fresh bundle checkout and archive verification -> deliver and complete goal.
