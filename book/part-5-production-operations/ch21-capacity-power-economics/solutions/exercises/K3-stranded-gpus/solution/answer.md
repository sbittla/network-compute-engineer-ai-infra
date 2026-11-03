# K3 — Stranded GPUs: worked solution

Source: manuscript Sections 21.2 ("Energized power"), 21.3 ("Capacity onboarding") and 21.7.

**Definition.** Stranded capacity is installed, paid-for capacity that cannot be used to run work.
It costs amortization, support and space every hour but never appears in allocated GPU-hours. In the
lab, 464 GPUs delivered in 2028Q2 wait for facility phase 2. At $3.00 per nominal GPU-hour that is
464 × 2,190 h × $3.00 ≈ $3.05M per quarter `[MODELED]` (Section 21.9, Step 6).

Two causes other than missing facility power, each with the telemetry that reveals it (any two of
these earn full marks):

| Cause | Mechanism | Telemetry that reveals it |
|---|---|---|
| **Network not ready** | Leaf groups not cabled, optics missing (often the long pole), or fabric validation not yet passed (Chapter 10). Nodes are powered but cannot join a backend job | Nodes absent from the scheduler partition or in a `DOWN`/`DRAIN` state with reason "fabric validation"; failing `ib_write_bw`/NCCL acceptance tests; switch ports administratively down |
| **Stuck in acceptance or repair** | Burn-in or acceptance failures, or a repair queue longer than the 5-day canonical MTTR (Chapter 16) | Lifecycle state counts over time (racked → burn-in → accepted → in service); age of nodes in `repair`; first-pass yield below the 95 % plan |
| **Cooling limit** | CDU capacity, pump redundancy lost or a supply-temperature excursion forces nodes off or capped | CDU heat load and supply/return temperatures near design; nodes drained with reason "cooling"; `HW_THERMAL_SLOWDOWN` clock-event reasons on a row |
| **Wrong GPU type for the demand** | An inference-only pool, or a GPU generation the training software does not support, sits idle while training queues | Per-pool allocation: one pool near 0 % allocated while another has a long queue |

**Common wrong answers**

- Counting fragmentation as stranding. Fragmented GPUs are in service but unusable for the job at the
  head of the queue: a scheduling loss, already a reserve in Section 21.2.
- Naming a cause without a signal ("bad planning"). The exercise asks for telemetry that would reveal
  it.
