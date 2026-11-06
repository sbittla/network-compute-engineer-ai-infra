# 20-R1 — When to accept a big bang: model answer

**Relies on:** manuscript Section 20.11, Step 6 (expected-loss comparison `[MODELED]`) and Table 20.14
(rollout shape trade-off).

## Model answer (≤ 150 words)

Step 6 found the big bang cheaper in expectation (≈ 246 vs ≈ 1,578 GPU-h; ORION's hybrid ≈ 618, batch only ≈ 314), because on
ORION every wave stalls the whole training gang (no spare nodes). Its bad case is 1,408 GPU-h plus a broken run
and every inference replica down at once. Accept it only when the tail is small or nobody is exposed to it:

1. The change is **reversible in seconds** (commit-confirm on the leaves, an A/B config slot), so the 4 h outage
   assumption does not hold.
2. It was **validated in an identical lab under representative load**: same SKU, firmware, switch OS.
3. The **fleet is idle** (no training state or SLO at risk), for example a scheduled full-cluster maintenance.
4. The owner **explicitly accepts the tail cost** in the change record.

Evidence needed: lab results under load, a rehearsed and timed revert, confirmation that no jobs or inference
replicas run, and the signed risk acceptance.

## Marking (5 points)

Conditions 3 · specific evidence 2. Deduct for "when it is cheaper" without addressing tail risk.
