# Measured revision budget

The earlier study's conservative accounting is $4.4250627. Its provider list cost was $0.8840541; these are different accounting measures. To keep the user's original $8 conservative ceiling, retain the larger historical amount.

Five GLM development runs consumed $0.14421616 provider-reported cost. The healthy independent GPT-5 scoring probe consumed $0.00425375. Small connectivity probes are covered by the remaining margin.

The first baseline cost $0.0121; a long development question cost $0.0553 with service trouble. Later pruner/recovery development attempts cost $0.0335/$0.0286. A planning allowance of $0.035 per agent run gives $2.52 for 72 runs. At $0.006 per GPT-5 score, scoring adds $0.432; allow about $0.2 for mechanism probes. Expected additional cost is about $3.15, with workload and cache variability.

The new unified meter has a $3.40 hard reservation ceiling covering formal agents, judges, retries and mechanism calls. Historical conservative amount + GLM development + judge probe + new ceiling = $7.97353261. It retains concurrent in-flight request reservations and conservative charges for unresolved transport failures. If the ceiling prevents completion, reconcile actual provider usage first and request an explicit increase if necessary. Account credit balance is separate from this project ceiling.
