# 11.12 (O3) — Failure-aware training workflow

Method: Section 11.12 (Young/Daly). τ_opt = √(2·C·MTBF); waste = C/τ + (τ/2 + R)/MTBF (first order,
valid for C, R ≪ τ ≪ MTBF); lost wall time per failure = τ/2 + R. Inputs: job MTBF 48 h (ORION-256)
and 3 h (ORION-XL) = 1,536 node-hours / nodes (docs/REFERENCE_CLUSTER.md), C = 45 s sync or 5 s async,
R = 900 s. All values `[MODELED]`.

| Scenario | τ_opt | Waste at τ_opt | Waste at 4 h | Failures/day | Lost s/failure | GPU-h/failure | GPU-h/day |
|---|---|---|---|---|---|---|---|
| ORION-256 sync | 3,944 s (65.7 min) | 2.80 % | 5.0 % | 0.5 | 2,872 | 204 | 102 |
| ORION-256 async | 1,315 s (21.9 min) | 1.28 % | 4.7 % | 0.5 | 1,557 | 111 | 55 |
| ORION-XL sync | 986 s (16.4 min) | 17.5 % | invalid (τ > MTBF) | 8 | 1,393 | 1,585 | 12,679 |
| ORION-XL async | 329 s (5.5 min) | 11.4 % | invalid | 8 | 1,064 | 1,211 | 9,688 |

Hand check: √(2 × 45 × 172,800) = √(1.555 × 10⁷) = 3,944 s. A 4-hour interval at XL is invalid: only
e^(−4/3) = 26 % of 4-hour intervals would finish without a failure.

**Waste decomposition at XL async:** C/τ = 1.52 %, τ/(2·MTBF) = 1.52 %, R/MTBF = 900/10,800 = 8.33 %.
Restart time dominates.

**Restart procedure** (Figure 11.6):

1. **Detect** — NCCL watchdog timeout, rank exit, or step-time SLO breach (e.g. p50 > 1.05 × baseline).
2. **Isolate** — map ranks to host/GPU/NIC (Section 11.8); collect flight-recorder dumps and stacks
   from all ranks; choose the smallest schedulable failure domain (node for TP = 8).
3. **Replace** — drain the node; on ORION-256 (no spares) wait for repair or restart at DP = 7 with
   batch/LR adjusted; at XL use a declared spare pool (a variation from the reference cluster).
4. **Restore** — the latest checkpoint whose metadata is durable and that passed a restore test.
5. **Validate** — loss continuity within noise, step time within 2 % of baseline, no per-rank outliers.

**Retry/quarantine policy.** Same node implicated twice → quarantine to Fleet for diagnostics; more
than 3 restarts per hour → stop the job and page; a node returns only after acceptance tests.

**Investment.** At 256 GPUs total waste is small (2.8 % sync); asynchronous checkpointing halves it
(1.3 %) cheaply — invest in **C**. At XL, R/MTBF is 8.3 of 11.4 points: invest in **R** (spare pool,
pre-pulled containers, faster NCCL bootstrap, parallel sharded restore) and in **MTBF** (burn-in,
proactive health checks that drain suspect nodes). Async C is necessary but not sufficient at XL.

**Common wrong answers.** Keeping a 4-hour interval at XL; using cluster MTBF per node instead of job
MTBF; forgetting R in lost work.
