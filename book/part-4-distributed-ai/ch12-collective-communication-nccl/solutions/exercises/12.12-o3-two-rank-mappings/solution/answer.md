# 12.12 (O3) — Two rank mappings: c2 (aligned) vs c3 (alternative map)

**(a) Prediction from topology, before looking at the plateau** `[MODELED]`:

```text
c2: 8 NICs per node, every GPU↔NIC path PIX, GPUDirect RDMA on
    ceiling = 8 × 50 GB/s = 400 GB/s;  × ≈ 0.88 ring efficiency → ≈ 350 GB/s
c3: NCCL_IB_HCA limited to mlx5_0–3 → 4 NICs per node
    ceiling = 4 × 50 GB/s = 200 GB/s;  × ≈ 0.92 (fewer, fatter channels per NIC) → ≈ 185 GB/s
    GPUs 4–7 reach NICs 2–3 across the inter-socket link (SYS): GPUDirect RDMA is disabled at that
    distance by default → staging through host memory → α higher by ≈ 5–15 µs
```

**(b) Data** `[SIMULATED]`: c2 plateau 352 GB/s, α 28.1 µs; c3 plateau 184 GB/s, α 39.2 µs. Both
predictions hold: c3 has ≈ 52 % of c2's plateau (4 of 8 NICs) and +11 µs of α. The deficit is steady
(low jitter), which points at mapping/topology rather than a degrading link (that is c6's signature).

**(c) Evidence to prove it on real hardware**

| Artifact | Command / source | Expected if hypothesis true | Falsified if |
|---|---|---|---|
| NICs NCCL uses | `NCCL_DEBUG=INFO`, line `NET/IB : Using [0]mlx5_0:1/RoCE …` | 4 devices listed in c3 | 8 devices listed |
| Environment | `cat /proc/<pid>/environ \| tr '\0' '\n' \| grep NCCL_` or the job template | `NCCL_IB_HCA=mlx5_0,…,mlx5_3` (and `NCCL_PXN_DISABLE=1`) | Variables unset; 8 devices; PXN enabled |
| Channel-to-NIC binding | INFO lines `Channel xx/0 : … via NET/IB/k[/GDRDMA]` | GPUs 4–7 via NET/IB/2–3 without `GDRDMA` | Every GPU via its own NIC with `GDRDMA` |
| GPU↔NIC path type | `nvidia-smi topo -m` | GPU4 ↔ mlx5_2 = `SYS` | `PIX` |
| Topology seen by NCCL | `NCCL_TOPO_DUMP_FILE=/tmp/topo.xml` | NICs 4–7 absent from the graph | All NICs present |
| Traffic per NIC | `ethtool -S` / `rdma statistic` tx counters during the run, or switch port counters | Rails 4–7 idle | All rails ≈ equal traffic |
| Intra-node control | Rerun 1- and 2-node tests with `NCCL_NVLS_ENABLE=0` | Intra-node part unchanged between c2 and c3 | c3's deficit disappears or changes with NVLS off |

**Conclusion.** c3's container image restricts NCCL to half the NICs and forces cross-socket paths
without GPUDirect RDMA. Fix: remove the `NCCL_IB_HCA` override (or set the full list), rerun c3, and
expect ≈ 350 GB/s; adopt an image lint for NCCL variables (Exercise 12.6).

**Common mistakes.** Explaining the halving by "congestion" without predicting it from NIC count;
listing evidence without a falsifying result.
