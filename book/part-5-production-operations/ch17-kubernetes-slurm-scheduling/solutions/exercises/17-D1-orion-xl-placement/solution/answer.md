# 17-D1 — ORION-XL block placement rules

**(a) Configuration.** Sixteen blocks of 32 nodes, each block one set of 8 rail leaves. A block is
the canonical ORION-XL pod (`p00`–`p15`), so the leaf groups carry the pod names (Section 17.5.6):

```ini
# [ILLUSTRATIVE] topology.conf
SwitchName=p00 Nodes=orionxl-n[001-032]
SwitchName=p01 Nodes=orionxl-n[033-064]
# ... p02 - p14
SwitchName=p15 Nodes=orionxl-n[481-512]
SwitchName=core Switches=p[00-15]
```

Kubernetes equivalent: Kueue Topology-Aware Scheduling. Label nodes with pod, block, and hostname;
define a `Topology` whose `levels` list those label keys widest to narrowest; reference it from the
`ResourceFlavor` (`spec.topologyName`); request per pod set with
`kueue.x-k8s.io/podset-required-topology: <block-label>` (all pods in one block) or
`...podset-preferred-topology` (best effort). API version and annotation names are
`[VENDOR-SPEC, 2026-10]`; verify against your Kueue release.

**(b) Placement comparison** `[MODELED]`. Minimum blocks for 64 nodes = 64 / 32 = 2. Model the
exposure as the fraction of ring hops that cross a block boundary, rail ring ordered
block-contiguously: crossings = number of blocks *b* (a closed ring crosses each boundary once
out and once back, b crossings in total) out of 64 hops.
- 2 blocks: 2 / 64 = **3.1 %** of hops on the spine
- 3 blocks: 3 / 64 = **4.7 %**
- free spread over 16 blocks (≈ 4 job nodes per block): P(next node in another block) ≈ 1 − 3/63 ≈
  **95 %**
Per-block uplink capacity at 2:1: 32 nodes × 8 rails × 400 Gb/s / 2 = **51.2 Tb/s**. Contiguous
placement puts only a few node-links of the job on the spine; spread placement puts nearly every
rail hop there, shared with ≈ 40 other jobs. These fractions are a ring-only lower bound: at 64
nodes NCCL may pick Tree or PAT, or run several rings per rail, and a tree crosses block boundaries
at every level, so real cross-block traffic is higher. **Rule:** require ≤ 2 blocks, allow 3 after a timeout,
never spread.

**(c) Wait bound.** Waiting *w* hours idles 512 GPUs → 512·*w* GPU-hours. A 3 % step slowdown
`[ILLUSTRATIVE]` from a worse placement over a 240 h run costs 0.03 × 240 × 512 ≈ **3,686
GPU-hours**. Break-even *w* = 3,686 / 512 ≈ **7.2 h**. A `--switches=2@04:00:00` (wait up to 4 h
for a 2-block placement, then accept 3) is defensible: it caps the waiting cost at 2,048 GPU-hours,
below the slowdown it avoids. Any bound with consistent arithmetic earns credit.

`solve.py` reproduces the fractions, uplink, and break-even.
