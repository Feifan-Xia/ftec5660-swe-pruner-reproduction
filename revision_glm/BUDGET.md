# Measured revision budget

## Current authorization

On 2026-11-11 the user explicitly approved a **$12 project total ceiling**, prioritizing completeness. The pinned-study meter allocation is **$6.756494**, after carrying $5.093506 of earlier conservative/development accounting and retaining a $0.15 margin. The machine-readable authorization is in `runs/glm/pinned/budget_authorization.json`. The pinned study uses a single Z.AI agent route and a single OpenAI judge route; earlier mixed-provider requests are preserved as development evidence.

The completed 72-run goal-shift study cost $0.07808792 in provider-reported usage. Its full/pruned/recoverable conditions cost $0.019846/$0.0226154/$0.03562652. Formal study spending remains available in the unified pinned ledger.

## Earlier planning under the $8 ceiling

The earlier study's conservative accounting is $4.4250627. Its provider list cost was $0.8840541; these are different accounting measures. To keep the user's original $8 conservative ceiling, retain the larger historical amount.

Five GLM development runs consumed $0.14421616 provider-reported cost. The healthy independent GPT-5 scoring probe consumed $0.00425375. Small connectivity probes are covered by the remaining margin.

The first baseline cost $0.0121; a long development question cost $0.0553 with service trouble. Later pruner/recovery development attempts cost $0.0335/$0.0286. A planning allowance of $0.035 per agent run gives $2.52 for 72 runs. At $0.006 per GPT-5 score, scoring adds $0.432; allow about $0.2 for mechanism probes. Expected additional cost is about $3.15, with workload and cache variability.

The new unified meter has a $3.40 hard reservation ceiling covering formal agents, judges, retries and mechanism calls. Historical conservative amount + GLM development + judge probe + new ceiling = $7.97353261. It retains concurrent in-flight request reservations and conservative charges for unresolved transport failures. If the ceiling prevents completion, reconcile actual provider usage first and request an explicit increase if necessary. Account credit balance is separate from this project ceiling.
