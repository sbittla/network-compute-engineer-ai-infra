# K1 — Step-time equation and evidence sources (solution)

**Equation (manuscript Section 22.1.2, Table 22.1):**

```text
T_step = T_compute + T_comm,exposed + T_bubble + T_data,exposed + T_host + T_ckpt,amortized
```

All six terms are required; `T_ckpt,amortized` is the checkpoint pause divided by the number of steps
between checkpoints, and `T_bubble` is the pipeline fill/drain fraction ≈ (p − 1)/(m + p − 1).

**Direct evidence for the two named terms on ORION:**

| Term | Direct measurement | Grain |
|---|---|---|
| `T_comm,exposed` | Nsight Systems timeline with NCCL ranges: the part of each collective kernel *not* overlapped by compute kernels. In production, the framework's per-rank collective-wait timer. | Per kernel (Nsight); per rank per step (framework timer) |
| `T_data,exposed` | The training loop's timer around fetching the next batch (`next(iterator)`), logged as `data_wait` per step. Supporting, not direct: dataloader worker stats, storage client latency, CPU iowait. | Per step per rank |

**Why these and not others.** The equation is about *exposed* time. A collective that runs fully under
the backward pass costs nothing, so the evidence must see overlap. NIC throughput, `DCGM_FI_PROF_NVLINK_TX_BYTES`
and switch counters measure bytes moved, not whether the GPU waited for them. Likewise, storage read
bandwidth says nothing about whether the prefetch buffer ran dry; only the loop timer does.

**Common wrong answers.**
- Naming NIC throughput or busbw as a measure of exposed communication (it ignores overlap).
- Naming iowait as the direct data-wait measure: it is host-wide and corroborating only.
- Writing five terms (forgetting the amortized checkpoint term or the bubble).

Evidence label: definitional; no numbers are claimed.
