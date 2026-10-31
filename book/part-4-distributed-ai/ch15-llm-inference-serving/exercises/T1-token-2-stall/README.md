# T1 — Token-2 stall in the disaggregated pool (★★★, L1)

Type: troubleshooting · Kind: written

## Prompt

<!-- prompt:start -->
**T1. ★★★ L1 (tabletop) — Token-2 stall in the disaggregated pool.** Halcyon AI runs W-INFER
disaggregated (6 prefill + 2 decode TP = 4 replicas; the decode replicas are on GPUs 0–3 of
`orion-n27` and `orion-n28`, nodes of the Kubernetes inference partition orion-n25–n32, so W-TRAIN is not
running at full size), with KV transfer over RoCEv2 on the backend rails. Every weekday
from about 14:00 to 15:30, the second-token latency (the first ITL gap) p99 climbs from 24 ms to
180 ms. TTFT and mean TPOT barely move, and the decode pool's KV usage is
normal. You have the following evidence `[ILLUSTRATIVE]`:

| Signal (decode-node rail ports) | 13:00–14:00 | 14:00–15:30 |
|---|---|---|
| RX throughput per decode node, sum of its rails 0–3 (Gb/s, 1 min avg) | 108 | 330 |
| ECN-marked packets/s (`orion-be-leaf-r0`–`r3` egress to decode NICs) | 40 | 31,000 |
| PFC pause frames received by decode NICs (per s) | 0 | 1,900 |
| KV transfer time p99 | 4.3 ms | 160 ms |
| Inference request rate | 39 req/s | 41 req/s |

The Slurm calendar shows a recurring 64-GPU fine-tuning job from 14:00 to 15:30. You do not know
which nodes it runs on.
(a) Walk the diagnostic loop: list ranked hypotheses, the discriminating test for each, and the
evidence you would still need. (b) Propose a safe immediate mitigation and a structural fix.
(c) State how you would validate the fix.
*Evidence required:* ranked hypotheses with for/against evidence, at least two discriminating
tests with real commands or data sources, a mitigation that touches no shared fabric
configuration without change control, and a validation criterion with numbers.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/incident_analysis.md`

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
