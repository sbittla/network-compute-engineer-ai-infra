# K3 — Paged KV cache: worked solution

**Problem solved (Section 15.5).** Before paging, servers reserved a *contiguous* KV region per request
sized for the maximum possible length (prompt + max output). Most requests stop early, so most of the
reservation is never written (**over-reservation**). Requests of different sizes leave holes between
regions (**external fragmentation**). The vLLM paper reports that only about 20–40 % of KV memory held
actual token state in prior systems. PagedAttention stores KV in fixed **16-token blocks** allocated on
demand through a block table, like virtual-memory pages. Waste is at most one partial block per
sequence, and blocks can be shared (prefix caching, beam search).

**New failure mode.** Because blocks are allocated *as sequences grow*, the scheduler admits more
sequences than could fit at full length. The pool can run out **while sequences are decoding**. The
engine must then **preempt** a running sequence:

- **Recompute:** free its blocks and later re-prefill prompt + generated tokens. For a 10k-token context
  on TP = 2 FP8 that is ≈ 0.88 s of prefill (K8), and the prefill stalls every co-scheduled sequence.
- **Swap:** copy its blocks to host memory over PCIe and back later. For 10k tokens it is 3.28 GB, ≈ 33 ms
  each way per GPU at ≈ 50 GB/s, plus host-memory pressure.

Either one stalls the replica. When a long-context tenant keeps the pool near 100 %, preemptions repeat:
a **preemption storm**. In the lab trace it shows as KV 98–100 %, a rising preemption counter, running
below the concurrency cap, and a queue forming with flat arrivals `[SIMULATED]`.

**Common wrong answer.** "Paging removes the memory limit." It removes waste, not the limit.
