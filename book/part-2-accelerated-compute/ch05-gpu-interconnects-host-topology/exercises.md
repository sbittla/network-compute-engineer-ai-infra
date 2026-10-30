# Chapter 5 — Exercises

Difficulty: ★ foundational · ★★ intermediate · ★★★ advanced. Tier: **L1** laptop/paper · **L2** single
GPU host · **L3** multi-node GPU + RDMA. Use ORION values ([REFERENCE_CLUSTER.md](../../../docs/REFERENCE_CLUSTER.md))
and Table 5.4 model parameters unless stated; label every number and show formula → substitution → result.

**Chapter deliverable (course outline):** *topology map, locality recommendations, and validation
checklist* — plus, from outline Section 20.4, *raw topology outputs, annotated topology diagram, mapping
CSV, benchmark methodology, measured results (if hardware is available), and explanation of
limitations*. Exercises 5.10 (lab) and 5.13–5.14 produce them.

---

## Knowledge checks

**5.1** ★ L1 — What does a PCIe BDF identify, and why is it not the same as a physical slot? Name two
ways to get the slot. *Evidence required:* definition and two commands/fields.

**5.2** ★ L1 — Give the legend meaning of PIX, PXB, PHB, NODE and SYS, and order them from best to worst for
GPU↔NIC RDMA traffic. *Evidence required:* five meanings and an ordering with one-line justification.

**5.3** ★ L1 — On `orion-n01`, `NIC1` in `nvidia-smi topo -m` is `mlx5_0` and is the rail-0 NIC. Explain
why the HCA index does not equal the rail number, and which source is authoritative for the rail.
*Evidence required:* probe-order explanation; LLDP/cabling database.

**5.4** ★ L1 — Why does every GPU pair show `NV18` on an HGX H100-class board, and what does that tell you
about GPU↔NIC locality? *Evidence required:* NVLink/NVSwitch arithmetic and the "nothing" answer.

**5.5** ★★ L1 — Explain what ACS Request Redirect does, why virtualized hosts want it, and why it hurts
GPUDirect RDMA on bare-metal training nodes. *Evidence required:* mechanism, isolation purpose, P2P cost.

**5.6** ★★ L1 — List the six GPUDirect RDMA prerequisites from Table 5.3 and the evidence that proves the
path is actually used at runtime. *Evidence required:* six items; the NCCL log signature.

**5.7** ★ L1 — Name three things that should be NUMA-local to a GPU and its NIC, and one command that
reveals each. *Evidence required:* three items with commands.

## Worked problems

**5.8** ★★ L1 — *PCIe budget.* (a) Compute per-direction theoretical bandwidth of Gen4 x16, Gen5 x8 and
Gen5 x16. (b) Which can carry a 400 Gb/s NIC at line rate? (c) An HX8 PCIe switch carries two GPUs and two
400 Gb/s NICs behind one Gen5 x16 uplink to the CPU. With GPUDirect RDMA, how much of the NIC traffic uses
the uplink? Without GDR (host-staged)? *Evidence required:* arithmetic for (a), justification for (b),
two traffic estimates for (c) with assumptions.

**5.9** ★★ L1 — *Modeled cost of one bad path.* Using the Section 5.9 formula with *S* = 1 GiB,
*n* = 256, *R* = 8, α = 0.2 ms and no variance: (a) busbw when every path is PIX (48 GB/s); (b) busbw when
one node has one NIC at PCIe Gen5 x8 (assume 27 GB/s achievable); (c) busbw when one node lacks GPUDirect RDMA on all
NICs (18 GB/s cap); (d) explain why (c) is worse than one would guess from "one node out of 32". (This
exercise deliberately uses a full 32-node, 256-rank W-TRAIN job, unlike the 16-node worked example.)
*Evidence required:* three results with arithmetic; one-paragraph explanation; label `[MODELED]`.

## Hands-on lab

**5.10** ★★ L1 (L3 extension) — Complete [Lab 5](lab/README.md): implement `topo_mapper.py`, pass
`python check.py`, produce the mapping CSV for all four hosts, a findings table, the scenario table, and
`topology_report.md`. *Evidence required:* per the lab rubric.

## Outline-mandated exercises

**5.11** ★ L1 — *Shortest GPU–NIC pairings.* Using Figure R.1 (REFERENCE_CLUSTER.md) and the `orion-n01`
`nvidia-smi topo -m` capture, list for each GPU the NIC with the shortest data path and its label, and
name one GPU–NIC pair of each class PXB, PHB, NODE and SYS. *Evidence required:* 8-row table plus four
examples, quoting matrix cells.

**5.12** ★★ L1 — *P2P versus host-staged.* For a 4 GiB transfer GPU2 → GPU6 on HX8: (a) list the copies,
memory locations and synchronization points for NVLink P2P and for a host-staged transfer with pinned
buffers; (b) repeat for pageable buffers; (c) estimate times with 370 GB/s NVLink and 52 GB/s PCIe per
direction, unpipelined and pipelined in 64 MiB chunks; (d) which socket's memory should host the staging
buffer, and why is that awkward here? *Evidence required:* annotated lists, four times, NUMA argument.

**5.13** ★★ L1 (L2/L3 to validate) — *Rank placement and its validation.* For a 2-node, 16-rank job on HX8
nodes with TP = 8 inside each node and DP = 2 across nodes, propose the rank→GPU→NIC→CPU mapping
(including `CUDA_VISIBLE_DEVICES`, CPU binding and NIC selection) and a validation plan that proves the
placement on hardware. *Evidence required:* mapping table, launcher settings, a validation checklist with
pass criteria and the commands/log lines used.

**5.14** ★★★ L1 / L3 — *Section 20.4 lab.* Produce an annotated topology diagram of one HX8 host, the GPU-to-HCA
mapping CSV, aligned and intentionally misaligned rank/rail maps, and a comparison of NCCL all-reduce
results — measured with nccl-tests if you have L3 hardware (lab README §8), otherwise from the labelled
model — with benchmark methodology and limitations. *Evidence required:* raw outputs, diagram, CSV, two
rank maps, results table with labels, methodology, limitations.

**5.15** ★★ L2 — *Prove GDR.* On a GPU host with an RDMA NIC, collect evidence for each Table 5.3 item,
then run a test that shows GDR in use (or not). *Evidence required:* raw command outputs per item,
NCCL `/GDRDMA` lines or `ib_write_bw --use_cuda` results, and a verdict.

## Troubleshooting case

**5.16** ★★★ L1 — After a rack move, eight ORION nodes were re-cabled. A 64-GPU job's busbw fell from
≈ 350 to ≈ 300 GB/s with p99 iteration time up 40 %; one node, `orion-n12`, shows these facts `[ILLUSTRATIVE]`:
LLDP for `enp153s0np0` → `orion-be-leaf-r5 Ethernet12`, for `enp163s0np0` → `orion-be-leaf-r4 Ethernet12`;
`nvidia-smi topo -m` golden; the leaf ports' interface counters clean; NCCL log shows all NICs in use with
`/GDRDMA`; the ORION backend in this pod runs as an **L2 rail VLAN** (not routed /31). Rank hypotheses,
identify the root cause, explain why the job still runs but slower, give a safe fix and validation.
*Evidence required:* ranked hypotheses with tests, root cause, traffic-path explanation, fix, validation.

## Design challenge

**5.17** ★★★ L1 — A cheaper node variant has 8 GPUs but only **4** × 400 Gb/s compute NICs, one per PCIe
switch (each switch: 2 GPUs + 1 NIC, each on its own downstream port, so both GPUs are `PIX` to the NIC). Design the rail architecture (4 or 8 rails?), the GPU→NIC mapping,
rank placement, and the NCCL/launcher settings; estimate the modeled busbw against HX8 for a 1 GiB
all-reduce over 32 nodes (a full-cluster job, unlike the 16-node worked example; state assumptions); and decide which workloads you would schedule on it.
*Evidence required:* topology diagram, mapping, model arithmetic, workload recommendation with a rejected
alternative.

## Reflection and review

**5.18** ★ L1 — Which parts of your lab results are raw observations, which are derived, and which are
modeled? What would make the modeled ones measured?

**5.19** ★ L1 — The model treats samples as independent per iteration. How would time-correlated slow
paths (a path slow for minutes) change p99 and the "nearest vs aligned" conclusion?

**5.20** ★★ L1 — Why should the mapping CSV be keyed by GPU UUID and NIC BDF rather than by GPU index and
HCA name? Give a failure that the index-keyed version would hide.

**5.21** ★ L1 — What could make `lstopo`-derived and `nvidia-smi`-reported relations disagree on a real
platform, and what would you do about it?

*Evidence required for 5.18–5.21:* short written answers (≤ 150 words each) citing specific mechanisms or data.
