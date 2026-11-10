# FTEC5660 SWE-Pruner reproduction

Deadline: 2026-11-10 24:00 Asia/Shanghai.

## Agreed scope
- Official SWE-QA multi-turn subset; full observations, original pruning, pruning with on-demand recovery.
- Three repetitions targeted; final sample count and budget follow pilot measurements.
- Pilot authorized up to USD 1. Formal experiment spending requires confirmation.
- Prefer user's OpenCode Go provider from CC Switch; verify endpoint and accounting first.
- English report <=10 pages, reproducible code/README/commits, raw evidence and figures, Chinese narration and demo script.
- User records presentation and submits. Public GitHub publication requires confirmation.

## Verified environment
- Upstream public commit: 96171b5f3ecaf89745cbeb436c8893b57f3400bd.
- Local upstream clone excluded from submission Git; preserve changes as patches or vendored attributed files.
- WSL Ubuntu-22.04 sees NVIDIA RTX 5060 Laptop GPU, 8151 MiB.
- WSL environment: /home/feifa/ftec5660-swe-pruner/.venv, Python 3.12.14.
- Torch 2.8.0 cu128 install started (exec session 95209).

## Evaluation requirements
- Separate pilot/development questions from fixed evaluation questions.
- Keep all selected tasks in primary results, including failures. Show author-filtered statistics separately.
- Count recovery and judge calls; preserve usage and timestamps.
- Record actual pruning, failures, repeated reads, and attention backend adaptations.
- OpenCode Go connectivity succeeded via official /inference/go/openai/v1, model deepseek-v4.1-flash. Response reports cash cost 0, billing_source go, allowance 0.00001782. Credential loaded from newest CC Switch opencode entry into ignored .env.
- Streamlink clone pinned to ab1f3656; official question JSONL includes reference answers. Task selection saved with source hash and seed; pilot and formal candidates disjoint.
- Official runner prepared with credential-safe config logging, serial execution, and user-agent/session headers.
- Live sessions: Torch install 95209; auxiliary dependencies 46358; model download 94597; SDK install 3620. Poll these handles before starting replacements.
- Observation store tests passed (2). Actual integration with OpenHands and model serving still pending.
