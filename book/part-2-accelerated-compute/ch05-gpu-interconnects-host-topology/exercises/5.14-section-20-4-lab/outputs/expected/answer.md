# 5.14 — Topology lab (Section 5.11): topology, rank maps and all-reduce comparison (marking guide)

Graded with the Lab 5 report rubric (30 points, see `meta.yaml`); the listed lab checks must PASS. Relies on
manuscript Sections 5.6, 5.8–5.10 and the lab README L3 section (nccl-tests procedure).

**Raw outputs and diagram (6).** The seven capture files of one host (or the learner's own L2 capture made
with `capture/capture_topology.sh`) and an annotated diagram: two sockets with their NUMA nodes and core
ranges; host bridges; four PCIe switch complexes, each with two GPUs and two backend NICs on their own
downstream ports; frontend NICs `mlx5_8`/`mlx5_9` on root ports; each NIC labelled with BDF, slot, NUMA node
and rail (from LLDP).

**Mapping CSV (6).** Keyed by GPU UUID and NIC BDF, with GPU index, HCA name, netdev, relation, slot, NUMA,
rail and an `aligned` flag. For `orion-n01` all 8 rows aligned and PIX.

**Rank maps (6).** Aligned: local rank *i* → GPU*i* → `mlx5_i` (PIX, rail *i*). Intentionally misaligned (the
lab README wrapper): local rank *i* → `mlx5_((i + 4) mod 8)`, i.e. a socket-1 NIC for socket-0 GPUs and vice
versa (SYS), with `NCCL_PXN_DISABLE=1` so NCCL cannot forward around it.

**Results table (6).** Either `[MEASURED]` (nccl-tests, 2 nodes, `-b 8 -e 8G -f 2 -w 20 -n 100`, ≥ 5 separate
launches per configuration, busbw median and spread at 1 GiB and 8 GiB, manifest with `NCCL_NET_GDR_LEVEL`,
`NCCL_PXN_DISABLE`, the per-rank HCA table and `/GDRDMA` lines; expect misaligned channels to lose `/GDRDMA`)
or `[MODELED]` with Table 5.4's parameters cited. Model reference for 16 nodes: S1 aligned 352.3 GB/s vs S2
cross-socket 40.8 GB/s (deterministic ≈ 142 GB/s at the 18 GB/s host-staged cap).

**Methodology and limitations (6).** One variable changed (NIC choice); drained nodes; interleaved runs;
warm-up; the model ignores inter-socket and uplink contention, spine congestion, protocol/algorithm choice
and time correlation; the lab files are simplified reconstructions; measured numbers apply only to the stated
manifest.

**Deduct** for unlabelled numbers, a CSV keyed by index, or modeled values presented as measurements.
