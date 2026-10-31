# 17-W2 — Priority versus fair share on the Monday queue

Dataset submit times (seeded jitter): J01 108 s, J05 304 s. Baseline: Table 17.7 / lab reference.

**1. Prediction with J01 at priority 100.** J10, J01, and J05 are now the priority-100 jobs. J10
(inference, share 27/48 = 0.5625) goes first. J01 and J05 are both pretrain at 100 with the same
share (96/160 = 0.600), so **submit time** breaks the tie: J01 (108 s) before J05 (304 s).
`[SIMULATED]`

| Job | Result | Reason |
|---|---|---|
| J01 (32) | n22, n24, n13, n18 | Rack-compact: rack-06 (2 whole-free) first, then rack-04 (n13), rack-05 (n18) |
| J05 (16) | Pending — InsufficientCapacity | No whole rail-complete node left; n20 6 + n21 6 = 12 < 16 eligible free |
| J08 (16) | Pending — InsufficientCapacity | Same: 12 < 16 |

Every other job is unchanged: J10, J12, J02, J07, J11, J13, J15, J09 placed; J03, J14
QuotaExceeded; J04 InvalidRequest; J06 Fragmentation.

**2. Comparison.** GPUs placed: baseline 4 + 16 + 8 + 8 + 16 + 4 + 2 + 8 + 1 + 2 = 69; variant
4 + 32 + 8 + 8 + 4 + 2 + 8 + 1 + 2 = **69, identical**. New GPUs per tenant:

| Tenant | Baseline | J01 at 100 |
|---|---|---|
| pretrain | 16 (J05) | 32 (J01) |
| research | 16 (J08) | **0** |
| finetune | 14 | 14 |
| inference | 15 | 15 |
| search | 8 | 8 |

Final usage in the variant: pretrain 128/160, research 18/48.

**3. Unintended consequence and a better policy.** The *urgent* release-candidate evaluation J05 is
now blocked by an ablation, because both share priority 100 and age breaks the tie; research, the
tenant furthest below its entitlement (0.375), gets nothing; utilization does not improve
(69 = 69). Better policy (any well-argued one earns credit):
- (a) a dedicated `urgent-eval` QOS above 100 with a small cap (`GrpTRES=gres/gpu=16`) so urgent
  evaluations always win but cannot monopolize (exercise 17-M2 replays this rule: J05 back on
  n22 + n24, research's J08 back on n13 + n18);
- (b) a gang **reservation** for the head-of-queue multi-node job at priority 50, so J01 is
  guaranteed the next four whole nodes (R-pt-002's 32 GPUs on n09–n12 when it ends) and other jobs
  backfill only if they do not delay it;
- (c) keep fair share for research.

**4. Verification.** Edit a copy of `job_queue.json` (J01 `priority: 100`) and run the simulator;
its output must match the table above. `solve.py` does exactly this with the reference simulator
and asserts the baseline, the variant, and the comparison.

**Common mistake:** assuming J05 still runs first because its note says "urgent".
