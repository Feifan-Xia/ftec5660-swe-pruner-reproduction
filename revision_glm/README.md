# Matched GLM-4.6 reproduction

This revision evaluates the released SWE-Pruner/OpenHands pipeline on the original eight-question Streamlink subset, three independent executions and three conditions: full observations, goal-conditioned pruning, and pruning with lossless observation recovery. The agent uses OpenRouter `z-ai/glm-4.6` restricted to Z.AI; the independent judge uses `openai/gpt-5` restricted to OpenAI. Provider fallback is disabled.

The primary modification is implemented by the reusable, standard-library-only `../observation_store.py` and the OpenHands adapter `../recovery_tool.py`. Stored text is the exact captured tool output. Expansion returns an inclusive, one-based range of at most 200 observation lines. An observation line can contain a file line number printed by `cat -n`; these are distinct coordinate systems.

## Reproduction procedure

Use a fresh clone so existing evidence remains intact. The root README describes the pinned upstream repository, Streamlink source, checkpoint downloads and Python environments. Apply its `prepare_upstream.py` compatibility patches first. The GPU environment needs the pinned dependencies in `requirements-pruner.txt`; the Linux agent environment uses `requirements-agent.txt` and `bubblewrap` (`bwrap`).

Create a clean read-only source snapshot in the Linux environment:

```bash
mkdir -p "$HOME/ftec5660-swe-pruner/glm-repository/streamlink"
git -C data/streamlink archive ab1f365 | tar -x -C "$HOME/ftec5660-swe-pruner/glm-repository/streamlink"
python revision_glm/prepare_runtime.py
python -m unittest discover -s revision_glm/tests -v
```

Set `FTEC_CLEAN_REPO` if the clean snapshot lives elsewhere. Bash commands run in a fresh `bwrap` namespace with the snapshot mounted read-only at `/workspace`. Host experiment files, reference answers, credentials and network access are outside this namespace.

Start the GPU service from the project root, in the GPU Python environment:

```powershell
.venv-pruner/Scripts/python.exe revision_glm/serve.py
```

The service uses the released checkpoint, threshold 0.5 and the original 8192-token model chunking. The additional SDPA adapter tiles the query axis while retaining every key/value and the causal mask; this bounds attention working memory without shortening the model context. `validate_attention.py` and `tests/test_attention.py` document and test this adaptation.

For the OpenRouter meter, set `OPENROUTER_API_KEY` through your local environment. On the author's workstation it can also read the selected CC Switch provider from the local database; `CC_SWITCH_PROVIDER_ID` overrides that local selection. Keys are never passed into the agent's shell. Set `JUDGE_HTTPS_PROXY` to a local HTTP proxy when required by the provider route, or an empty string for a direct connection. The original run used a separate local proxy on port 7898; proxy subscription credentials are excluded from artifacts.

```powershell
python revision_glm/meter.py --limit YOUR_APPROVED_RUN_LIMIT_USD
```

The meter listens on `127.0.0.1:8879`, reserves an upper cost bound for concurrent requests and persists provider-reported usage. Its directory is `runs/glm/pinned/`. An explicit `budget_authorization.json` in that directory may update the limit; the historical file records the user's approval and the accounting carried from earlier development. Choose a fresh run's own budget rather than copying the historical authorization.

Freeze the runtime and launch the agent study from Linux:

```bash
python revision_glm/freeze.py
python revision_glm/run_study.py --workers 3
```

The runtime hash check verifies the exact files used by the schedule. Existing completed attempts are reused; incomplete attempts require process diagnosis before resuming. All first attempts are retained. One additional agent attempt is allowed for a missing answer, a process failure or a pruning-service failure. Low judge scores never trigger agent retries. Judge transport/schema failures have a separate bounded retry policy.

Run the separate, predefined goal-shift experiment:

```bash
python revision_glm/recovery_probe.py
```

It samples eight eligible plugin files using seed 5660 before model calls. Each original observation is filtered for an import-inspection goal; the follow-up asks for a specific string constant. Full, pruned and recoverable observations are compared over three executions. Exact string match is scored directly. All sampled cases remain in the analysis, including targets preserved by pruning.

After all planned runs finish:

```bash
python revision_glm/analyze.py
python revision_glm/analyze_mechanism.py
python revision_glm/analyze_recovery.py
python revision_glm/verify_repository.py
python revision_glm/audit.py
```

Both final analyzers require all 72 planned cells. `--partial` is reserved for progress inspection. Formal execution records live under `runs/glm/pinned/formal/`; request bodies, raw responses and usage are in the enclosing pinned directory. The exact launch sources and their hashes are archived with the formal study. Earlier DeepSeek and mixed-provider development records retain their original locations and are analyzed separately.

## Measurement definitions

- **Quality:** the released five-dimension SWE-QA rubric, scored by GPT-5; report the full planned population first and the authors' filtered paired statistic separately.
- **Cumulative tokens:** provider-reported prompt plus completion tokens, including cached input. The skimmer's source-token counts use its own tokenizer and describe a different quantity.
- **Rounds:** the authors' `stats.py` definition counts agent/user-source events. API request count is also reported explicitly.
- **Recovery:** successful range reads, total expansion tool actions, returned characters and repeated lines are retained separately.
- **Uncertainty:** repeated executions at temperature zero plus a paired bootstrap over eight question clusters. The three executions do not imply three explicitly controlled provider seeds.

The published Streamlink GLM row is the numerical reference. Scope, provider serving implementation, SDK version, judge deployment, the read-only repository snapshot and numerical adaptations are documented differences. The report interprets measured discrepancies using the recorded trajectories.
