# Marking scheme: K8 Why a diagnostic rollback is a poor test

Type knowledge-check · kind written · tier L1 · 4 points

**Evidence required:** two distinct reasons (confounding/time variation; information value vs cost/risk).

| Criterion | Points |
|---|---|
| Reason 1: confounding and time variation; the before/after of a rollback mixes it with everything else that changed | 2 |
| Reason 2: low information per cost and risk compared with offline partitions (one leaf, slow, drains/reboots) | 1 |
| Notes that the rollback destroys the natural experiment (half upgraded, half not) | 1 |
