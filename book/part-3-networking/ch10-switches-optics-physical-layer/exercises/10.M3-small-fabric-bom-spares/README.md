# 10.M3 — Ports, cables, and spares for a small leaf-spine fabric (★★, L1)

**Type:** Outline-mandated · **Kind:** computed · **Points:** 10

## Prompt

<!-- prompt:start -->
**10.M3 (Outline) — Ports, cables, and spares for a small leaf-spine fabric (★★, L1).**
A 24-node HX8 pod (8 GPUs and 8 × 400G backend NICs per node), rail-optimized, 1:1, 64-port 400G
switches, 400G-DR4 on every link. Estimate: leaves, spines, uplinks per leaf per spine, host links,
fabric links, optics, cables, leaf and spine ports used and free, and spares (3 % optics, 2 % cables,
minimum 2 per type, one spare switch per model). Identify the operational spares beyond optics and
cables. What happens to the spine layer if the pod grows to 32 nodes?
*Evidence required:* every quantity with its formula; a spares list; ≤ 80 words on growth. You may
check your numbers with the lab's `estimate_fabric_bom()`.
<!-- prompt:end -->

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: the worked answer: formula, substitution, result with units, decision sentence
- `outputs/work.py`: optional: a script that reproduces your numbers

Show every formula, substitution and result with units, and label each number with its evidence label.
