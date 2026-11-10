# SWE-Pruner reproduction with recoverable tool observations

FTEC5660 individual reproducibility project. The experiment uses the authors' SWE-QA/OpenHands pipeline on a fixed Streamlink subset, and adds an explicit tool for recovering saved original observations. The shared `ObservationStore` is intended for the XJ13 tool-observation study.

## Experiment status

Development runs are in progress. Formal evaluation and final report are pending. See `PROJECT_STATUS.md` for verified progress and `DEBUG_DIARY.md` for repairs. Results must be interpreted at their recorded model, repository revision, question subset, and configuration.

## Conditions

1. `baseline`: authors' full-output Bash tool.
2. `pruner`: authors' goal-conditioned pruning tool, released 0.6B weights, threshold 0.4.
3. `recovery`: the same pruning tool plus an observation ID and an `expand` tool returning exact requested original lines (`ExpandObservation` registration).

Original observations are scoped to a task process. The recovery tool permits at most 200 lines per call and logs overlapping reads. All groups share the agent, model, question, and execution limits.

## Sources

- [SWE-Pruner paper](https://arxiv.org/abs/2601.16746), Table 2: SWE-QA Streamlink.
- [Authors' code](https://github.com/Ayanami1314/swe-pruner), commit `96171b5f3ecaf89745cbeb436c8893b57f3400bd` (MIT).
- [Streamlink](https://github.com/streamlink/streamlink), commit `ab1f3656` (BSD-2-Clause).
- Questions and reference answers: authors' `downstream_eval/multi_turn/sweqa/questions/streamlink.jsonl`.

## Setup

Use Linux/WSL, Python 3.12 and an NVIDIA GPU. Run these repository preparation commands from this project's root in WSL:

```bash
GIT_LFS_SKIP_SMUDGE=1 git clone https://github.com/Ayanami1314/swe-pruner upstream
git -C upstream checkout 96171b5f3ecaf89745cbeb436c8893b57f3400bd
mkdir -p data
git clone --filter=blob:none https://github.com/streamlink/streamlink data/streamlink
git -C data/streamlink checkout ab1f3656
bash scripts/setup_wsl.sh
```

The setup script requires `uv` on PATH and creates a separate agent environment under `~/.venvs/ftec5660-agent`. `requirements-agent.txt` records the tested installed versions. Set the environment location with the script's first argument if desired.

For the Windows GPU service, reuse a Python 3.12 environment whose PyTorch can allocate a tensor on the GPU. With its interpreter path in `$GpuPython`, run:

```powershell
& $GpuPython -c "import torch; print(torch.__version__, torch.cuda.is_available()); print(torch.ones(1, device='cuda'))"
uv venv --python $GpuPython --system-site-packages .venv-pruner
uv pip install --python .venv-pruner/Scripts/python.exe -r requirements-pruner.txt
.venv-pruner/Scripts/python.exe -m huggingface_hub.cli.hf download ayanami-kitasan/code-pruner --revision 863cee3198c715c9df1faa422a3490e0832bb734 --local-dir models/code-pruner --include '*.json' '*.txt' 'model.safetensors'
.venv-pruner/Scripts/python.exe -m huggingface_hub.cli.hf download Qwen/Qwen3-Reranker-0.6B --revision e61197ed45024b0ed8a2d74b80b4d909f1255473 --local-dir models/qwen-backbone --include config.json
.venv-pruner/Scripts/python.exe serve_pruner.py
```

Check the download route and existing cache first. The released weights occupy approximately 1.35 GB; a fresh GPU runtime can add several GB. Prefer direct access or the designated non-metered VPN route for downloads above 5 GB. Model file revisions, sizes and SHA-256 hashes are recorded in `configs/model_assets.json`. The exact tested nightly PyTorch build is recorded in `configs/environment_gpu.json`; availability of that historical build on a fresh machine is not guaranteed. A replacement GPU runtime requires re-running the numerical and demo checks.

`python prepare_upstream.py` applies documented compatibility and accounting fixes. The script is idempotent. The tested GPU service uses an existing Windows PyTorch 2.9.0.dev20250705+cu129 installation, Transformers 4.57.1, BF16 stored weights and the upstream FP16 autocast. SDPA replaces Flash Attention, unused attention weights are omitted, and single-example inference omits masked right-padding. The agent runs separately in WSL Ubuntu 22.04 / Python 3.12 / OpenHands SDK 1.1.0. WSL mirrored networking accesses the Windows services through localhost.

`validate_pruner.py` compares attention kernels and padding to 8192 on two fixed probes. All token decisions at threshold 0.4 agreed; probabilities differed by up to 0.01653. This is a limited numerical sensitivity check. Exact bitwise equivalence and broader equivalence remain unproven. The setup script now installs only the agent environment; GPU dependencies are managed separately.

Create a local `.env` using `.env.example`. Keep credentials outside Git.

## Run

Start `serve_pruner.py` in the GPU environment (port 8000) and the budget proxy on port 8877. Run task/scoring commands in the WSL agent environment:

```bash
python budget_proxy.py --limit 1 --port 8877
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
python validate_pruner.py  # GPU environment
python demo.py             # Running local GPU service; no paid API
```

Raw logs and downloaded assets are excluded from Git during development. The final publication package will include a reviewed, credential-free evidence bundle, environment lock, report and demo script.
