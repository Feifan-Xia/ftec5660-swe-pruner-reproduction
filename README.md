# SWE-Pruner reproduction with recoverable tool observations

FTEC5660 individual reproducibility project. The experiment uses the authors' SWE-QA/OpenHands pipeline on a fixed Streamlink subset, and adds an explicit tool for recovering saved original observations. The shared `ObservationStore` is intended for the XJ13 tool-observation study.

## Experiment status

Development runs are in progress. Formal evaluation and final report are pending. See `PROJECT_STATUS.md` for verified progress and `DEBUG_DIARY.md` for repairs. Results must be interpreted at their recorded model, repository revision, question subset, and configuration.

## Conditions

1. `baseline`: authors' full-output Bash tool.
2. `pruner`: authors' goal-conditioned pruning tool, released 0.6B weights, threshold 0.4.
3. `recovery`: the same pruning tool plus an observation ID and `ExpandObservation` tool returning exact requested original lines.

Original observations are scoped to a task process. The recovery tool permits at most 200 lines per call and logs overlapping reads. All groups share the agent, model, question, and execution limits.

## Sources

- [SWE-Pruner paper](https://arxiv.org/abs/2601.16746), Table 2: SWE-QA Streamlink.
- [Authors' code](https://github.com/Ayanami1314/swe-pruner), commit `96171b5f3ecaf89745cbeb436c8893b57f3400bd` (MIT).
- [Streamlink](https://github.com/streamlink/streamlink), commit `ab1f3656` (BSD-2-Clause).
- Questions and reference answers: authors' `downstream_eval/multi_turn/sweqa/questions/streamlink.jsonl`.

## Setup

Use Linux/WSL, Python 3.12 and an NVIDIA GPU. Clone upstream with `GIT_LFS_SKIP_SMUDGE=1`, check out the pinned commit, and download `ayanami-kitasan/code-pruner` into `models/code-pruner`. Clone Streamlink into `data/streamlink` and check out the pinned commit.

`python prepare_upstream.py` applies documented compatibility and accounting fixes. The script is idempotent. GPU installation uses PyTorch 2.8.0 CUDA 12.8 and Transformers 4.57.1; SDPA replaces the original Flash Attention backend. See `scripts/setup_wsl.sh` for the current machine-specific setup commands; a portable verified environment lock will accompany the final package.

Create a local `.env` using `.env.example`. Keep credentials outside Git.

## Run

Start the local pruner on port 8000 with the downloaded model and the budget proxy on port 8765:

```bash
python budget_proxy.py --limit 1
python run_task.py --mode baseline --index 43
python run_task.py --mode pruner --index 43
python run_task.py --mode recovery --index 43
python score_results.py runs/pilot/baseline/q43_r0
python summarize_results.py --phase pilot
```

Use the appropriate completed attempt path when scoring. `configs/task_selection.json` records disjoint development and evaluation indices, sampling seed, and source hash. Formal runs require a recorded budget approval in `configs/formal_approval.json`.

## Measurements

The loopback proxy records provider usage for every request, separately preserving input/output tokens, cash cost, and Go allowance consumption. A conservative uncached peak-price ceiling controls pilot spending. Agent run tokens are aggregated from these per-request records. Judge calls have separate session IDs.

The official five-dimensional rubric is retained. Current pilot scoring uses the same model as the agent and is marked accordingly; final analysis must describe this evaluator limitation. Execution failures remain in the primary task inventory. Author-filtered scores are secondary.

## Validation

```bash
python -m unittest discover -s tests -v
```

Raw logs and downloaded assets are excluded from Git during development. The final publication package will include a reviewed, credential-free evidence bundle, environment lock, report and demo script.
