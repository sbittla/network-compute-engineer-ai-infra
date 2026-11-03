# 2.2 — ORION-128 small-cluster BOM

Method: manuscript Sections 2.3–2.5 (rack layout, the three networks, circuit arithmetic). Inputs are the
exercise's `[ILLUSTRATIVE]` assumptions; every result is `[MODELED]` and reproduced by `solve.py`.

## 1. Nodes per rack and racks

```text
usable per circuit = √3 × 415 V × 32 A × 0.80 × 0.95 = 23.00 kVA × 0.76 = 17.48 kW
per side (2 circuits)                                = 34.96 kW
need for n nodes   = (10.2 n + 0.2) × 1.10
n = 3 : 30.8 × 1.10 = 33.88 kW ≤ 34.96  ✓ (headroom 1.08 kW)
n = 4 : 41.0 × 1.10 = 45.10 kW > 34.96  ✗
```

**3 nodes per rack.** 128 GPUs / 8 = 16 nodes → ⌈16 / 3⌉ = **6 GPU racks**. A balanced 4 × 3 + 2 × 2
layout leaves headroom in two racks. A full rack holds 3 × 8U = **24U** of nodes.

## 2–5. BOM

| Item | Quantity | Formula |
|---|---:|---|
| GPU nodes | 16 | 128 / 8 |
| GPU racks | 6 | ⌈16 / 3⌉ |
| Rail leaves (64-port) | 8 | one per rail |
| Host-to-leaf links | 128 | 16 nodes × 8 rails |
| Leaf uplinks (1:1) | 16 per leaf | = 16 downlinks per leaf |
| Leaf-to-spine links | 128 | 8 × 16 |
| Spines (64-port) | 2 | 128 spine ports / 64; each leaf 8 uplinks to each spine |
| Backend links, total | 256 | 128 + 128 |
| Switch ports used | 384 | leaves 8 × 32 = 256; spines 2 × 64 = 128 |
| Leaf ports unused | 256 | 8 × 64 − 256 |
| 400G transceivers (all optical) | 512 | 2 per link: 128 at NICs, 384 at switches |
| Bisection per direction | 25.6 Tb/s | 128 × 400 Gb/s / 2 at 1:1 |
| Frontend node ports (200G) | 32 | 16 × 2 |
| OOB ports | 56 | 16 BMCs + 10 backend switches + 2 frontend leaves + 4 storage + 6 × 4 PDUs |

**Spine-count justification:** 128 leaf uplinks need 128 spine ports; two 64-port spines provide exactly
128, and 8 leaves × 8 uplinks = 64 ports per spine, so every leaf reaches every spine equally.

**Note on the unused ports:** half of every leaf is idle because a rail-optimized design needs one leaf per
rail regardless of node count. 32-port-class leaves, or carrying several rails per leaf where the
platform supports it, would save cost at this size.

## 6. Assumption to verify before ordering

The **10.2 kW node maximum and the 10 % transient margin at 32 A circuits**: the rack design has only
1.08 kW per side of headroom, so a ≈ 3 % error in node power (x ≤ 3.2 % from (30.6 × (1 + x) + 0.2) ×
1.10 ≤ 34.96) (or a firmware change that raises the GPU limit) breaks it. Measure the node's maximum
with a burn-in at the BMC before committing (the L2 lab extension). Also acceptable: whether the older
hall's floor and cooling accept ≈ 31 kW racks.

**Common wrong answers:** 4 nodes per rack (sizing on sustained power or forgetting the margin); copying
ORION's 4 spines; forgetting the unused leaf ports.
