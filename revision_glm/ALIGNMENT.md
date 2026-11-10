# GLM-4.6 revision: evidence and decisions

The user requests a rigorous same-model reproduction, complete fair comparisons, analysis of every experiment, and a meaningful isolated modification. Completion takes priority over the original midnight deadline, explicitly extended on 2026-11-10. Earlier DeepSeek results remain archived as supplementary evidence.

## Alignment discovered before the new formal experiment

- Paper: arXiv:2601.16746v1, Appendix D.1 states temperature 0, pruning threshold 0.5, and maximum 250 interaction rounds. The checked-in SWE-QA runner instead defaults to 50 rounds and 1800 seconds. These are distinct sources; the new formal design will use the paper's 250-round and 0.5-threshold settings, while documenting the implementation's time guard.
- The initial GLM development smoke uses the runner default 50 rounds. It is a baseline development question and does not establish the formal protocol.
- Agent: exact model ID `z-ai/glm-4.6` via OpenRouter, with actual endpoint/provider metadata recorded when available. A shared model name reduces the model mismatch; provider serving differences remain an explicit limitation.
- Official SWE-QA scoring comments name GPT-5, while executable code takes the deployment from CLI/environment and calls chat completions. Use OpenRouter openai/gpt-5 with the exact five-dimensional prompt; low reasoning effort is an explicitly recorded route adaptation. A successful scoring probe verified availability through a dedicated local SakuraCat US route.
- Fixed authors' code revision and Streamlink revision remain as recorded in the original selection file. The released skimmer weights and GPU numerical checks are retained.
- A separate runtime copy recognizes `FinishAction` by type when its name is null. Output capacity is 16384 tokens in the development proxy, recorded explicitly; complete the development checks before freezing formal settings.

## Main questions the report must answer

1. Does the matched GLM experiment reproduce the reported quality/token trade-off? Compare measured score, input/output tokens and interaction rounds with the exact Streamlink paper row; distinguish the experimental population and score filtering denominator.
2. Why do observed differences occur? Analyze per-question variation, pruning activation, retained source tokens, repeated repository reads, context growth, finalization and failures. Separate measured relationships from causal hypotheses.
3. What changes when exact recovery is available? Preserve all other condition settings; compare end-to-end quality/resources and controlled fixed-context recovery cases. A successful component demonstration alone is insufficient evidence of downstream benefit.

## Isolated modification

Task-scoped lossless storage plus explicit line-range expansion. Hypothesis: recovery can repair missing evidence after aggressive filtering and reduce repeated searches at a measurable extra context cost. Measure autonomous activation, correctness/completeness, additional tokens, repeated reads, and exact recovered content. Keep model replacement and compatibility fixes as shared reproduction setup.

## Failure policy

All attempts and repairs remain visible. Fix reproducible infrastructure defects during development, then freeze a uniform formal runtime. For execution/infrastructure failures, use separately identified recovery attempts with recorded reasons and a shared policy across conditions. Preserve first-attempt and recovered-completion analyses. Low answer quality alone never triggers a replacement. If a failure remains after bounded diagnosis, report the actual unresolved cause and effect on comparisons.

## Authorization

OpenRouter usage was approved by the user. The existing project ceiling remains $8 until a concrete revised estimate is approved. The new pilot has a $0.30 local guard; account balance is not spending authorization. Scope and expected formal/judge costs will be estimated from measured development runs before formal launch.

## Development fixes verified before formal launch

- CPU/GPU-independent shell boundary: bubblewrap exposes the pinned clean repository read-only at /workspace and hides host references, answers and API keys. All three conditions share this boundary.
- First long GLM pruning pilots exposed unavailable-service and 60-second-timeout / GPU-memory failure. Preserve these development attempts, exclude them from formal estimates of pruning efficacy.
- Query-axis tiled SDPA retains all keys/values and full causal masks. At 2813/4096 tokens the measured probabilities match full SDPA exactly on two fixtures; 7044-token tile-256 and tile-512 also match. The long path takes approximately 6.5 seconds and 4.54 GiB peak. Tests cover causal, padding and grouped-query attention.
- At threshold 0.5, masked-padding sensitivity changes one token decision on the second old numerical probe; report this numerical limitation explicitly. Line-level downstream equivalence is not established by token checks alone.
- Live recovery integration at threshold 0.5 pruned 6959 source tokens to 693 and recovered original lines 1–100 exactly. This validates implementation before outcome experiments.
- Authors stats.py counts all agent/user-source events as rounds. Report that exact definition alongside API request count.
