# 11.14 — The quiet 8 %

**Map the ranks first** (Section 11.8). Ranks 96–103 → node ⌊96/8⌋ = 12 → `orion-n13`, all eight local
ranks: exactly one TP group. With r = tp + 8·dp + 64·pp, 96 = 0 + 8 × 12 → dp = 12 mod 8 = 4,
pp = ⌊96/64⌋ = 1: **PP stage 1, DP replica 4**. Every other rank waits for it — at the pipeline
boundaries ("pp_wait") and in DP collectives — which is why 248 ranks show ≈ 1.3 s more wait.

**Ranked hypotheses**

1. **Node-level power/thermal limit on `orion-n13`** — all 8 GPUs equally slow, compute only, TP and DP
   comm unchanged. Fits everything, including `SW Power Cap: Active`.
2. **Data imbalance** — plausible in principle because all 8 TP ranks of a group process the same
   micro-batches; test it rather than assume.
3. **Host CPU contention** (kernel-launch starvation after maintenance, e.g. a runaway agent).
4. **Degraded NVLink on `orion-n13`** — would raise TP comm time, which is unchanged: rejected.

**Discriminating tests**

| Test | Expected if (1) | Result that rejects (1) |
|---|---|---|
| `nvidia-smi -q -d PERFORMANCE` on n13 vs a peer | n13: `SW Power Cap: Active`; peer: not active | No clock-event reason active |
| `nvidia-smi -q -d POWER` | Power limit lowered (e.g. 500 W vs 700 W default) | Default limit |
| `nvidia-smi --query-gpu=clocks.sm,power.draw,power.limit,temperature.gpu --format=csv` | SM clocks ≈ 9 % lower, draw pinned at the limit, normal temperature | Same clocks as peers |
| Per-rank token counts from the data loader | Identical to peers (rejects 2) | n13 ranks process more tokens |
| `top`/`mpstat` on n13 | Normal CPU | Saturated cores (supports 3) |

**Root cause.** A power limit left in place by the firmware-maintenance procedure on `orion-n13`.

**Safe fix.** Checkpoint; drain `orion-n13`; Fleet restores the default power policy under change
control and runs acceptance tests before returning the node. ORION-256 has no spares, so either wait
(fast if it is only a power limit) or restart at DP = 7 (224 GPUs, batch/LR adjusted). The training job
is not the place to change power policy.

**Validation.** Step p50 back to 17.45 s over ≥ 200 steps; ranks 96–103 compute within 1 % of the
median; power limit = default on the returned node; add a post-maintenance power-limit check to the
acceptance suite.

**Cost** `[MODELED]`: expected step 17.45 + 1.3 × 131/128 = 18.78 s (stem 18.8 s); throughput loss
1 − 17.45/18.78 = 7.1 % of 256 GPUs × 24 h = **≈ 435 GPU-h per day**.

**Common wrong answer.** Blaming the fabric because "everyone is waiting in collectives".
