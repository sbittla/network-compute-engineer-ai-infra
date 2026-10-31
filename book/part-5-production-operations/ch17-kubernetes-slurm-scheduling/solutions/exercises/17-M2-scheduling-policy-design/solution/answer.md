# 17-M2 — ORION scheduling policy (model answer)

**1. Eligibility filters, in order** (cheapest and most decisive first; the diagnoser uses the same
order): lifecycle `schedulable` → health (not `failed`/drained) → pool (`train` / `infer`) → GPU
type (`nvidia.com/gpu.product` label / Slurm `Feature`) → dedication (taint *and* selector) → MIG vs
whole GPU → rail completeness for multi-node jobs (Slurm feature `rails8` + `--constraint`, or Kubernetes
label `halcyon.ai/rails-complete=true` with required affinity; never a drain).

**2. Topology.** 1/2/4-GPU jobs: socket-aligned best fit (keep the other socket whole). 5–8 GPU jobs:
one node, best fit. > 8 GPUs: whole nodes only and a multiple of 8, else InvalidRequest. Prefer
rail-degraded nodes for single-node 8-GPU work. Gangs: rack-compact on ORION; ≤ 2 blocks on ORION-XL
(17-D1).

**3. Quota.** Nominal GPUs per tenant (ClusterQueue / QOS `GrpTRES`); borrowing within a cohort only
into idle capacity, ≤ 1.2× nominal overcommit; borrowed capacity is reclaimable.

**4. Priority and preemption (asymmetric).** Classes: serving 100, `urgent-eval` QOS 110 capped at
16 GPUs, standard training 50, best-effort 10, scavenger 5. Serving may preempt best-effort; training
is preemptible only in a `requeue` QOS (cost: 80 GPU-hours per preemption of a 128-GPU job, 17-W1).

**5. Fairness key:** priority class, then dynamic share (used/quota), then age. **6. Gang mechanism:**
all-or-nothing admission (Slurm allocation / Kueue); the head-of-queue multi-node job gets a node
reservation and others only backfill if they do not delay it. **7. Small jobs:** confined to
shared/partial nodes in the training pool (best fit already packs them onto n20/n21/n29) so whole
rail-complete nodes stay whole.

**8. Metrics:** gang time-to-start p50/p95; largest placeable gang over time; allocation %;
fragmentation (free GPUs not in whole nodes); quota-blocked job-hours; preemptions per week.

**Replay evidence for one rule: the `urgent-eval` QOS** `[SIMULATED]`, lab snapshot seed 17.
*Before* = the pretraining lead's proposal (J01 at priority 100, 17-W2): J01 n13 + n18 + n22 + n24;
J05 (urgent eval) and J08 (research) InsufficientCapacity; research gets 0 new GPUs.
*After* = same queue with J05 in `urgent-eval` (priority 110): J05 n22 + n24, J08 n13 + n18, J01
InsufficientCapacity; research gets 16, pretrain 16; GPUs placed 69 in both runs.
Interpretation: the rule restores urgent work and research's fair share without losing
utilization; J01's wait is then addressed by rule 6 (reservation), which the single-pass simulator
cannot show (17-R1). `solve.py` runs both replays with the reference simulator and asserts them.
