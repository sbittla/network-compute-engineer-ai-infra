# 13.18 — Locality mistakes hidden by idle benchmarks: worked solution

**Mistakes that pass an idle benchmark** (Section 13.5):

1. **Cross-socket NIC use** (GPU 6 using NIC 2, `SYS`). GDR is lost and traffic crosses the
   inter-socket link. On an idle node the link has spare capacity and `ib_write_bw` may still reach
   near line rate.
2. **Cross-rail placement.** A rank's traffic leaves on rail *i* and must reach rail *j* through a
   backend spine (`orion-be-spine-1`…`orion-be-spine-4`). In a two-node test the spine is empty and adds only ≈ 1–2 µs.
3. **NUMA misbinding.** NCCL proxy threads, data-loader workers or pinned buffers on the wrong socket.
   An idle benchmark does not load the memory controllers, so the extra hop costs little.
4. **Interrupts and IRQ affinity on one socket.** Invisible until both NICs and the loader are busy.

**Why production exposes them.** Production adds *contention*: the data loader uses the same DRAM and
socket link, all 8 GPU/NIC pairs transfer at once, and other jobs share the spine. The inter-socket link
and spine stop having spare capacity, so misaligned paths slow down, and they do so *variably*.
Synchronous training converts that variance into stragglers: every collective waits for the slowest of
thousands of transfers, so a path that is 10 % slower 5 % of the time sets the step time at scale
(1 − 0.95^N → 1 for large N, Section 13.7).

**Implication.** Validate locality by *configuration* (`nvidia-smi topo -m`, rank→NIC map, `numactl
--show` per rank, NCCL `/GDRDMA` lines) and by loaded tests, all 8 pairs concurrently with background
DRAM traffic. Idle point-to-point bandwidth is not enough.
