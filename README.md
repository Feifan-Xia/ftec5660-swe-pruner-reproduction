# FTEC5660 SWE-Pruner Reproduction

Xia Feifan · 1155204948

This repository reproduces a bounded result from SWE-Pruner and evaluates one small modification: task-local recovery of pruned Bash observations.

## Final result

The completed study contains eight fixed Streamlink questions, three repeats, and three conditions, for 72/72 answered, scored and metered cells.

| Condition | Mean quality | Mean cumulative tokens | Mean requests | Pruning activation |
|---|---:|---:|---:|---:|
| full output | 9.00 | 136.4K | 12.71 | 0% |
| focus-question pruning | 9.12 | 112.3K | 10.46 | 25% |
| pruning + recovery | 9.24 | 125.1K | 11.08 | 16.7% |

Main reproduction result:

- Pruning reduces mean cumulative API tokens by 17.6%.
- Mean quality changes from 9.00 to 9.12.
- Pruning activates in 6 of 24 tasks.
- The authors' same-question records reduce tokens by 49.9%. The difference is explained by hint coverage and investigation path length.

Modification result:

- Recovery raises mean quality from 9.12 to 9.24 (+1.4%).
- Recovery raises mean tokens from 112.3K to 125.1K (+11.3%).
- Recovery activates in 3 of 24 tasks and returns 51,480 characters through 12 successful reads.

The final reports are:

- [English report](report/revised/swe_pruner_reproduction_en.pdf)
- [Chinese report](report/revised/swe_pruner_reproduction_zh.pdf)

## Reproduction target

The target is the SWE-Pruner Streamlink result in Table 2 of the paper. The study keeps the released pruning checkpoint, line-selection threshold and 8192-token model chunking. It compares:

1. full tool observations;
2. original optional-hint pruning;
3. original optional-hint pruning plus bounded recovery.

The primary metric is cumulative API tokens over the complete agent path. Quality uses the released five-dimensional SWE-QA rubric. Request count and investigation rounds are reported separately.

## Modification

`observation_store.py` saves each captured Bash observation for the lifetime of one task. `recovery_tool.py` exposes an `expand(observation_id, start, end)` call with these rules:

- observation IDs are content hashes;
- ranges are inclusive and one-based;
- each call returns at most 200 lines;
- invalid ranges remain in the recorded request history;
- recovered characters and extra tool turns enter task cost.

The modification is isolated from the pruning checkpoint. It changes evidence access without changing the skimmer model or pruning threshold.

## Repository layout

| Path | Purpose |
|---|---|
| `observation_store.py` | Standard-library observation store |
| `recovery_tool.py` | OpenHands recovery adapter |
| `revision_glm/` | Frozen fixed-eight execution pipeline |
| `revision_optional/` | Recovery-condition execution and analysis |
| `revision_full/` | Final evidence reconciliation and audits |
| `results/full/manuscript_evidence.json` | Unified numbers used in the report |
| `results/full/author_same_questions.json` | Author/local same-question mapping |
| `report/revised/` | Final report sources, PDFs and figure |
| `tests/` | Store, recovery, ledger and terminal-history tests |

Raw runs, model weights, virtual environments and credentials are intentionally excluded from Git. The final report identifies the preserved evidence paths.

## Setup

Use Linux/WSL, Python 3.12 and an NVIDIA GPU.

```bash
export GIT_LFS_SKIP_SMUDGE=1
git clone https://github.com/Ayanami1314/swe-pruner upstream
git -C upstream checkout 96171b5f3ecaf89745cbeb436c8893b57f3400bd

mkdir -p data
git clone --filter=blob:none https://github.com/streamlink/streamlink data/streamlink
git -C data/streamlink checkout ab1f3656

bash scripts/setup_wsl.sh
```

The setup creates a separate agent environment under `~/.venvs/ftec5660-agent`.

For the Windows GPU service, use a Python 3.12 environment with a working CUDA PyTorch build:

```powershell
uv venv --python $GpuPython --system-site-packages .venv-pruner
uv pip install --python .venv-pruner/Scripts/python.exe -r requirements-pruner.txt
```

Download the released checkpoint and backbone:

```powershell
.venv-pruner/Scripts/python.exe -m huggingface_hub.cli.hf download ayanami-kitasan/code-pruner --revision 863cee3198c715c9df1faa422a3490e0832bb734 --local-dir models/code-pruner --include '*.json' '*.txt' 'model.safetensors'
.venv-pruner/Scripts/python.exe -m huggingface_hub.cli.hf download Qwen/Qwen3-Reranker-0.6B --revision e61197ed45024b0ed8a2d74b80b4d909f1255473 --local-dir models/qwen-backbone --include config.json
```

Apply the frozen runtime compatibility fixes:

```powershell
python prepare_upstream.py
```

## Run

The full execution procedure is documented in `revision_glm/README.md` and `revision_full/README_CURRENT.md`.

The essential sequence is:

```powershell
# GPU service
.venv-pruner/Scripts/python.exe revision_glm/serve.py

# Meter, in another terminal
python revision_glm/meter.py --limit YOUR_APPROVED_RUN_LIMIT_USD
```

```bash
# Linux/WSL agent study
python revision_glm/freeze.py
python revision_glm/run_study.py --workers 3
```

API credentials are read from local environment variables and are never committed.

## Recompute the final evidence

```powershell
python -X utf8 revision_precision/analyze.py
python -X utf8 revision_optional/analyze.py
python -X utf8 revision_full/audit_subset.py --study precision --repeats 3
python -X utf8 revision_full/audit_subset.py --study optional --repeats 3
python -X utf8 revision_recovery/audit_reads.py --study optional
python -X utf8 revision_full/compare_author_same_questions.py
python -X utf8 revision_full/summarize_evidence.py
```

Render the reports:

```powershell
python -X utf8 report/revised/render.py report/revised/swe_pruner_reproduction_en.md report/revised/swe_pruner_reproduction_en.pdf --language en
python -X utf8 report/revised/render.py report/revised/swe_pruner_reproduction_zh.md report/revised/swe_pruner_reproduction_zh.pdf --language zh
```

## Tests

```powershell
python -X utf8 -m unittest tests.test_observation_store tests.test_subset_recovery tests.test_terminal_history tests.test_meter_transport
```

## Evidence and limitations

- All 72 selected cells have answers, scores and transmitted-request usage.
- First-attempt completeness is 81.9%; documented infrastructure retries produce final completeness of 100%.
- Failed attempts, judge retries and recovered branches remain separate in the evidence archive.
- The result covers eight fixed questions and does not claim the paper's full Streamlink population.
- The authors' records use a different serving path and investigation policy.
- Quality intervals include zero, so the recovery quality gain is directional rather than conclusive.

## Pinned sources

- Paper: <https://arxiv.org/abs/2601.16746v1>
- SWE-Pruner: <https://github.com/Ayanami1314/swe-pruner>
- Streamlink: <https://github.com/streamlink/streamlink>
- Checkpoint: <https://huggingface.co/ayanami-kitasan/code-pruner>

## Course submission

The recorded presentation is 12:14 long and demonstrates the reproduction result, the recoverable-pruning modification and the live recovery command. The final course submission also includes the eight-page report PDF.
