# Corrected reproduction and evidence map

## Completed scope

Latest small-scope diagnosis: see `GAP_FINDINGS.md`. Complete author-input replay (131 observations) isolates skimmer fidelity; `results/full/trajectory_gap_audit.json` measures hint/path discrepancies. A disjoint first-request priming screen completes six cells and fails its frozen quality gate (−37.7% tokens, −10.3% quality). Its frozen protocol and sources are in `revision_priming/` and `runs/priming/formal/`. The reference audit preserves two source/reference disagreements without replacing official scores. Full-population expansion is deferred; approved budget remains USD12, current conservative USD9.4687.

Recompute this extension with `revision_priming/analyze.py`, `revision_full/analyze_priming.py`, `revision_full/audit_subset.py --study priming --repeats 1`, `revision_full/audit_development_references.py`, and `revision_full/summarize_gap.py`. The reference audit reads the pinned checkout under `data/paper-workspace/`; its saved JSON embeds cited source excerpts and hashes for archive-only review.

The corrected fixed subset contains eight questions × three repetitions × full, original optional-hint pruning and optional-hint recovery: 72 complete executions. A required-hint diagnostic contributes 24 executions and the corrected controlled recovery experiment contributes 72. Full Streamlink expansion remains pending; its prepared schedule contains the remaining 40 questions × three conditions × three repetitions.

| Evidence | Location |
|---|---|
| Full and original pruner, 48 executions | `runs/precision/formal`, `results/precision` |
| Original-hint recovery, 24 executions | `runs/optional/formal`, `results/optional` |
| Required-hint full / pruner / recovery | `runs/hintfull`, `runs/hint`, `runs/recovery/formal` |
| Controlled recovery, 72 trials | `runs/recovery/mechanism`, `results/recovery/mechanism.json` |
| Terminal-only replay, two affected prefixes | `runs/full/terminal_repair`, `results/full/terminal_repair_analysis.json` |
| Author-run same-question reference | `results/full/author_same_questions.json` |
| Unified manuscript numbers | `results/full/manuscript_evidence.json` |
| Chinese and English drafts | `report/revised/subset_draft_zh.pdf`, `subset_draft_en.pdf` |

The historical `revision_glm` results describe earlier settings and remain separately labeled. Frozen launch files are copied into each study's `formal/frozen_source` directory and verified by `runtime_manifest.json`. `VARIANTS.md` explains the small differences between frozen variants.

## Recompute the completed evidence

Use the full evidence archive, which includes `runs/`; the code-only repository intentionally excludes raw runs and credentials. From the project root, using Python with `httpx`, `pypdf`, `reportlab`, `matplotlib` and `PyMuPDF` installed:

```powershell
python -X utf8 revision_precision/analyze.py
python -X utf8 revision_hint/analyze.py --partial
python -X utf8 revision_hintfull/analyze.py
python -X utf8 revision_recovery/analyze.py
python -X utf8 revision_optional/analyze.py
python -X utf8 revision_full/analyze_terminal.py
python -X utf8 revision_full/compare_author_same_questions.py
python -X utf8 revision_full/summarize_evidence.py
python -X utf8 revision_full/audit_subset.py --study precision --repeats 3
python -X utf8 revision_full/audit_subset.py --study optional --repeats 3
python -X utf8 revision_recovery/audit_reads.py --study optional
python -X utf8 report/revised/build_subset_draft.py
python -X utf8 report/revised/build_english_draft.py
python -X utf8 report/revised/render.py report/revised/subset_draft_zh.md report/revised/subset_draft_zh.pdf --language zh
python -X utf8 report/revised/render.py report/revised/subset_draft_en.md report/revised/subset_draft_en.pdf --language en
```

The required-hint protocol initially allowed three repetitions; only its predeclared eight-question first screen was launched. Its analyzer's `--partial` preserves that larger frozen protocol while the completed diagnostic uses repetition zero. The original main comparison and optional recovery each require all three repetitions. Eight question clusters, rather than 48 clusters, are used in the bootstrap; the frozen precision protocol's old prose is corrected in `DIAGNOSIS_V2.md`.

Report rendering uses installed Windows SimSun, Microsoft YaHei Bold and Times fonts. Latin/mathematical runs use Times to preserve the mathematical minus and subscript glyphs. Every PDF has a maximum of ten pages. Figures are generated from result JSON by `report/revised/plot_precision.py` and `plot_mechanism.py`.

## Fresh execution environment

Use a fresh checkout and evidence directory for independent reruns. The root README supplies upstream/checkpoint setup and the existing dependency files. The upstream code pin is `96171b5f3ecaf89745cbeb436c8893b57f3400bd`; the code-pruner checkpoint pin is `863cee3198c715c9df1faa422a3490e0832bb734`. The GPU environment uses `requirements-pruner.txt` with the validated CUDA PyTorch installation; the recorded build is `2.9.0.dev20250705+cu129`. The Linux agent environment uses Python 3.12, `requirements-agent.txt` and `bubblewrap`.

`prepare_paper_workspace.py` obtains the pinned source-only repositories under `data/paper-workspace/swe-repos`. Copy that `swe-repos` directory into `$HOME/ftec5660-swe-pruner/paper-workspace/` in Linux. Keep Conan, Reflex and Streamlink together. The frozen runner mounts this shared source root read-only at `/workspace`, with evaluation answers and credentials outside the tool sandbox. Existing source/checkpoint caches can be reused; this setup does not require reinstalling a working CUDA stack.

Run `revision_full/serve_fp32.py` in the GPU environment. Its health endpoint on port 8000 must report `torch.float32`, 8192-position padding and `sdpa-query-tiled-256`. The service serializes GPU pruning. Frozen agents check the service before using it.

Supply `OPENROUTER_API_KEY` through a private local environment. `revision_full/meter.py --limit YOUR_APPROVED_LIMIT` starts the metered service on port 8879. Set `AGENT_HTTPS_PROXY` and `JUDGE_HTTPS_PROXY` to the intended local proxy URLs or empty strings for direct routes appropriate to the provider account. Provider routing remains fixed to Z.AI for GLM-4.6 and OpenAI for GPT-5, with fallback disabled. The workstation-specific transport wrapper records the route used in this study; independent machines should configure their own supported network route.

The meter uses `runs/full/budget_authorization.json` when present. Historical reconciliations are tied to the preserved historical ledger; copying that offset into a fresh empty ledger would invalidate the limit. A fresh run starts with its own ledger and approved budget. The meter records request bodies and responses without bearer headers. The agent's tool sandbox receives neither API keys nor the meter's files.

On a fresh run, freeze before launching:

```bash
python revision_precision/freeze.py
python revision_full/resume_subset.py --study precision --workers 3 --repeats 3
python revision_optional/freeze.py
python revision_full/resume_subset.py --study optional --workers 3 --repeats 3
```

The corrected runtime preserves original optional hints and applies `fix_terminal_history.py` in new recovery runs. The historical precision runtime preserves released terminal behavior for exact provenance. Replaying a repaired terminal branch uses its saved request and identical agent-visible prefix, with original and repaired outputs retained.

## Recovery and integrity rules

Every selected execution requires all transmitted-request usage receipts, an exported answer and a valid score. Low scores retain their first qualified execution. Network failures preserve the original attempt and use the bounded infrastructure policy. Judge-only resumption can target `--cell q8_r2`; its exclusive lock prevents concurrent evaluation of the same answer. `reconcile_duplicate_judges.py` restores the first-valid-score rule from immutable request responses if a historical duplicate exists.

Exact reads are audited against content hashes, inclusive ranges, the 200-line bound, character counts and overlap. Initial visibility includes both pruned and full observations. Failed expansion requests remain in the trajectories and token totals. QA execution completeness and controlled exact-match SR have separate meanings and denominators.

```powershell
python -X utf8 -m unittest tests.test_subset_recovery tests.test_terminal_history tests.test_observation_store tests.test_meter_transport
```

The pure storage module and OpenHands adapter are the modification's implementation boundary. Diagnostic wrappers, numerical adapters and serialization repairs are explicitly identified so their effects can be assessed independently.
