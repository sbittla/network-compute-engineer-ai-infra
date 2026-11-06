# 7.W1 — Design a rail-optimized ORION-384 backend (★★, L1)

Type: Worked problem · kind: `computed` · 12 points

## Prompt

<!-- prompt:start -->
**7.W1** ★★ L1 **[Outline: design a two-tier leaf-spine for a specified number of GPU racks and
calculate uplink/downlink ratios]** — Halcyon plans **ORION-384**: 12 GPU racks × 4 HX8 nodes
(48 nodes, 384 GPUs, 8 × 400G backend NICs per node), 64 × 400G switches.

(a) Design a **rail-optimized, 1:1** two-tier backend. Give leaves per rail, total leaves, spines,
links per leaf-spine pair, used/total downlink ports, downlink:uplink ratio per leaf (as configured
and as used), host and fabric cable counts, and transceivers (all-optical, before spares).
(b) Run your lab's `size_two_tier(384, 64, 64, 1.0)`. Explain why its answer differs from (a).
(c) An inference-only variant would accept 3:1. Size it rail-optimized and state the cross-leaf
capacity per leaf against its downlink capacity.
(d) What changes about ECMP's importance in (a) compared with ORION-256?
*Evidence required:* every count with arithmetic; a one-paragraph explanation for (b) and (d).
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) for the ORION-256 backend, and the Section 7.3 conventions (Table 7.2).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare your method with the worked solution and marking scheme in the chapter's `solutions/exercises/7.W1-orion-384-design/` (instructor material in the full repository; removed from student releases).

## What to submit

Show every count with its arithmetic; label every number `[MODELED]`. Use your own lab implementation for (b). Put every deliverable in `outputs/`:

- `outputs/answer.md`
- `outputs/size_two_tier.txt` (the dict your lab returns for part (b))

Run:

```bash
cd ../../lab/starter && python -c "import fabric_lab as f; print(f.size_two_tier(384, 64, 64, 1.0))"
```
