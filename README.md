# SWE-Pruner: GLM-4.6 reproduction and exact observation recovery

FTEC5660 individual project · Xia Feifan · 1155204948.

This project runs the authors' SWE-QA/OpenHands pipeline on eight fixed Streamlink questions. Three conditions share GLM-4.6, the repository, the questions and generation settings: full observations, SWE-Pruner, and SWE-Pruner with exact recovery. Each condition is executed three times per question. A separate 72-cell goal-shift experiment measures whether the added tool can recover evidence removed from the current context.

## Read the results

- [Chinese report](report/glm/SWE-Pruner_report_zh.pdf) and [English report](report/glm/SWE-Pruner_report_en.pdf).
- [Audited aggregate results](results/glm/analysis.json), [per-run measurements](results/glm/cells.json), [mechanism results](results/glm/mechanism.json), and [integrity audit](results/glm/audit.json).
- [Protocol](revision_glm/protocol.json), [paper alignment](revision_glm/ALIGNMENT.md), and [reproduction instructions](revision_glm/README.md).
- [Chinese recording script](demo_script_zh.md) and [submission checklist](SUBMISSION_CHECKLIST.md).

The numerical reference is the paper's Table 2, Streamlink with GLM-4.6: score 8.56 in both conditions and 54.4% lower cumulative tokens with pruning. The report compares the local measurements with that result and explains task coverage, serving and scoring differences. Historical DeepSeek and mixed-provider development records are retained separately; the revised primary comparison uses a fixed Z.AI provider with fallback disabled and threshold 0.5.

## Final primary results

All 72 primary cells completed on their first agent attempt and were independently scored. The 72-cell mechanism study also completed. The integrity audit passes.

| Source and condition | Answers | Mean score / 10 | Mean cumulative tokens |
|---|---:|---:|---:|
| Paper, full observations | Published Streamlink aggregate | 8.56 | 318,200 |
| Paper, SWE-Pruner | Published Streamlink aggregate | 8.56 | 145,100 |
| Reproduction, full observations | 24/24 | 8.63 | 112,796 |
| Reproduction, SWE-Pruner | 24/24 | 9.27 | 130,950 |
| Reproduction, pruner + exact recovery | 24/24 | 9.13 | 139,798 |

The manuscript places published and reproduced values in Table 3, with within-study changes, rounds and uncertainty. Local results cover eight selected questions and three executions; the paper reports its Streamlink population. Method, experimental setup, results, discussion and conclusion form the main text; implementation adaptations and artifact details appear in Appendix A.

Pruning increases cumulative tokens by 16.1% in this subset despite compressing actually pruned source text by 76.5%. Long unfiltered investigations, especially q11, dominate the discrepancy with the paper. Recovery adds 6.8% tokens versus pruning, with a −0.13 score change. Seventeen successful expansions expose new nonblank lines in sixteen cases; one trajectory reconstructs a whole file. The report provides paired intervals, per-question evidence and scoring sensitivity.

## The modification

`observation_store.py` saves exact captured tool text per task. `recovery_tool.py` adds an observation ID and inclusive one-based `expand` ranges, capped at 200 lines per call, to the authors' pruning tool. Every recovery records returned characters and overlapping reads. The agent can request missing evidence without executing the original command again.

The independent goal-shift experiment supplies the same saved code observations after an import-inspection query, then asks for a string constant. Exact-match outcomes are full 24/24, pruned 3/24, recoverable 24/24. Recoverable observations use 55,617 cumulative tokens versus 24,082 for full observations. The report separates this controlled evidence-access result from autonomous repository QA, where the agent can also reread files.

The standard-library store is reusable in XJ13:

```python
from observation_store import ObservationStore

store = ObservationStore(max_lines_per_read=200)
text = '{\n  "answer": 42\n}'
observation_id = store.put(text)
assert store.expand(observation_id, 1, 3) == text
read_audit = store.manifest()
```

Instantiate a store per task. Ranges refer to saved observation lines; file line numbers printed inside a tool output are a separate coordinate system. The adapter's process-global store is task-scoped by the runner's one-process-per-attempt lifecycle. Integration into a multi-task server requires a separate store for each task.

## Pinned sources

- [Paper](https://arxiv.org/html/2601.16746v1), Table 2 and Appendix D.1.
- [SWE-Pruner](https://github.com/Ayanami1314/swe-pruner), commit `96171b5f3ecaf89745cbeb436c8893b57f3400bd`, MIT.
- [Streamlink](https://github.com/streamlink/streamlink), commit `ab1f3656`, BSD-2-Clause.
- [Released skimmer](https://huggingface.co/ayanami-kitasan/code-pruner), revision `863cee3198c715c9df1faa422a3490e0832bb734`.

## Setup

Use Linux/WSL, Python 3.12 and an NVIDIA GPU. Run these repository preparation commands from this project's root in WSL:

```bash
export GIT_LFS_SKIP_SMUDGE=1
git clone https://github.com/Ayanami1314/swe-pruner upstream
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
.venv-pruner/Scripts/python.exe revision_glm/serve.py
```

Check the download route and existing cache first. The released weights occupy approximately 1.35 GB; a fresh GPU runtime can add several GB. Prefer direct access or the designated non-metered VPN route for downloads above 5 GB. Model file revisions, sizes and SHA-256 hashes are recorded in `configs/model_assets.json`. The exact tested nightly PyTorch build is recorded in `configs/environment_gpu.json`; availability of that historical build on a fresh machine is not guaranteed. A replacement GPU runtime requires re-running the numerical and demo checks.

`python prepare_upstream.py` applies documented compatibility and accounting fixes. The script is idempotent. The tested GPU service uses an existing Windows PyTorch 2.9.0.dev20250705+cu129 installation, Transformers 4.57.1, BF16 stored weights and the upstream FP16 autocast. SDPA replaces Flash Attention, unused attention weights are omitted, and single-example inference omits masked right-padding. The agent runs separately in WSL Ubuntu 22.04 / Python 3.12 / OpenHands SDK 1.1.0. WSL mirrored networking accesses the Windows services through localhost.

## Run and verify the revised experiment

Follow [revision_glm/README.md](revision_glm/README.md) to create the clean read-only repository snapshot, start the GPU service and OpenRouter meter, freeze the runtime, and run all 72 primary cells plus the separate 72-cell mechanism study. Use a fresh clone and a new run directory for a new experiment. Keep API credentials in local environment variables.

Final analysis and evidence checks:

```bash
python revision_glm/analyze.py
python revision_glm/analyze_mechanism.py
python revision_glm/analyze_recovery.py
python revision_glm/verify_repository.py  # Linux/WSL snapshot verification
python revision_glm/audit.py
python -m unittest discover -s tests -v
python -m unittest discover -s revision_glm/tests -v
```

The shell isolation and final-answer tests run in Linux/WSL; run `test_attention.py` in the GPU environment. Reports are generated from the audited statistics and reviewed interpretation with `report/glm/figures.py`, `compose.py` and `render.py`. The renderer uses Windows Microsoft YaHei/Arial fonts. Reproducing report rendering requires those fonts or an explicitly selected replacement.

`revision_glm/package.py` creates the final local ZIP with the current code, bilingual reports, exact raw experiment evidence, file hashes, third-party licenses and a Git history bundle. It scans configured credentials and verifies all archived file hashes. Model weights and private local proxy configuration remain outside the package. `python scripts/verify_bundle.py PATH_TO_ZIP` independently checks the archive.

The source commit used at experiment launch and its exact archived files are recorded in `runs/glm/pinned/formal/runtime_manifest.json`. Subsequent commits add analysis, reporting and packaging. Recording, GitHub publication and course submission are completed by the student.
