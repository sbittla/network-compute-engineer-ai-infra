# 12.14 — Latency doubled, bandwidth fine

**Signature.** 8 B: 95 vs 47 µs (2.0×); 1 MiB: 118 vs 53 µs (2.2×); plateau 344 vs 345 GB/s (unchanged);
`#wrong` = 0; only the container image changed. Something added a *fixed per-collective cost* without
touching link bandwidth — software, not fabric.

**Ranked hypotheses**

1. **Algorithm/protocol restricted in the new image** (`NCCL_ALGO=Ring` or `NCCL_PROTO=Simple`). On 64
   ranks a ring's latency grows as 2(n − 1)·α_step while the default tree is log-depth; Simple has the
   highest latency of the three protocols (12.4). Large messages already use Ring/Simple, so the plateau
   is unaffected. Fits exactly.
2. **Proxy-thread or launch overhead** from CPU affinity or frequency changes in the image (processes
   bound to the wrong NUMA node, a different `OMP`/`numactl` wrapper). Raises latency, usually modestly
   and with more jitter.
3. **Different NCCL version with a tuning regression** (the image bundled a new NCCL).
4. **Network latency increase** (ECN/PFC or congestion-control change). Unlikely: no node or fabric
   change, and it would usually dent bandwidth too.

**Discriminating tests** (on a reserved node set; read-only first)

| Test | Command | Expected if (1) |
|---|---|---|
| NCCL sees an override | `NCCL_DEBUG=INFO NCCL_DEBUG_SUBSYS=ENV,TUNING all_reduce_perf -b 8 -e 8G -f 2` | A line such as `NCCL_ALGO set by environment to Ring` (format varies by version) |
| Version | Same INFO log, banner `NCCL version 2.x.y` | Same version as before (rejects 3 if equal) |
| Environment diff | `docker run <old> env \| grep NCCL_` vs `<new>` | `NCCL_ALGO`/`NCCL_PROTO` present only in the new image |
| Causal test | Rerun with the variable unset (`env -u NCCL_ALGO …`) | 8 B time back to ≈ 47 µs |
| Affinity | `numactl --show`, `taskset -cp <pid>` per rank | Unchanged (rejects 2) |

**Most likely root cause (model answer).** The new image's entrypoint exports `NCCL_ALGO=Ring`, left over
from a debugging session.

**Safe fix.** Remove it from the image under change control (new image tag, reviewed diff); do not
patch running jobs. Add an image lint that rejects `NCCL_ALGO`/`NCCL_PROTO` in production images
(Exercise 12.6) and include the `NCCL_*` environment in the benchmark manifest.

**Validation.** Five launches of the nightly 8-node suite: 8 B time 47 ± 3 µs, 1 MiB ≈ 53 µs, plateau
345 ± 2 % GB/s, `#wrong` = 0; INFO log shows no environment-set algorithm; the fix noted in the
incident record.

**Common wrong answer.** Opening a fabric ticket: bandwidth is fine and nodes did not change.
