# DC — Shared versus dedicated inference capacity: model recommendation

Method: the trade-off criteria of manuscript "Trade-offs and design decisions", the W-INFER analysis
of Section 1.9 and the goodput economics of Section 1.7. Costs at $3.00/GPU-hour (Chapter 21's TCO
rate per nominal GPU-hour); results `[MODELED]`, reproduced by `solve.py`. Either option earns full credit if
well argued.

**Recommendation: Option B, a dedicated eight-node inference pool on the frontend network only**,
revisited if the conditions below change. The new pool is Halcyon's *second*; the default pool
(`orion-n25`–`n32`) already serves W-INFER.

| Criterion | A: share 8 of the 24 training nodes | B: dedicated frontend-only pool |
|---|---|---|
| SLO risk | Higher: handover and preemption latency when training reclaims nodes; shared power envelope | Lower: isolated scheduling and capacity |
| Training capacity | Partition shrinks from 24 to 16 nodes; a full-size W-TRAIN run must borrow both inference pools | Unchanged (24 nodes) |
| Utilization | Higher if training can absorb idle inference capacity | Idle off-peak capacity is wasted |
| Hardware cost | Pays for 64 backend NICs, 64 rail-leaf host ports and 128 optics (both link ends) that inference does not use | Avoids those, plus the matching leaf-uplink/spine capacity if the fabric stays 1:1 |
| Scheduler | Slurm and Kubernetes must coordinate ownership of the same nodes | Kubernetes only |
| Failure domain | Shared with the training partition (a training-side fault or drain hits inference) | Separate |

**Quantified argument.** 8 nodes × 8 = 64 GPUs. The pool costs 64 × $3.00 × 8,760 h = **$1,681,920
per year** either way. If inference averages 60 % of the pool `[ILLUSTRATIVE]`, sharing could
reclaim at most 0.40 × 64 × 8,760 × $3.00 = **$672,768 per year** of training capacity. That is an
upper bound reached only if training can use preemptible 1–8-node fragments, which large synchronous
jobs such as W-TRAIN (all 32 nodes) cannot; with Option A that run must borrow both inference pools.
Realistically only small evaluation or fine-tuning jobs fit, so the reclaimable value is a fraction
of that, while every reclaim risks the TTFT/TPOT SLO.

**What the backend fabric is and is not needed for.** W-INFER at TP = 8 stays inside one `HX8`: its 160
all-reduces per step ride NVLink, and per-request network traffic is KB-scale and goes through the
frontend. RDMA is needed only for multi-node model parallelism (models that do not fit one node) or
disaggregated prefill/decode with KV cache transfer over RDMA (Chapter 15).

**Assumptions.** Capacity need is eight nodes' worth of W-INFER (≈ 8 × 3,370 tokens/s in decode);
$3.00/GPU-hour covers hardware, power and facility; average inference load 60 %; training jobs are mostly
full-cluster synchronous; the facility can host a separate pool.

**Would change my mind if:** inference demand is strongly diurnal *and* Halcyon runs many small,
preemptible training or evaluation jobs that can fill 1–8-node fragments; a disaggregated-serving design
needs RDMA KV transfer; or the facility cannot power or cool a separate pool (Chapter 2).

**Common wrong answers:** claiming inference needs the RDMA fabric at TP = 8; counting the full $1.7 M as
saved by sharing; ignoring the Slurm/Kubernetes ownership problem.
