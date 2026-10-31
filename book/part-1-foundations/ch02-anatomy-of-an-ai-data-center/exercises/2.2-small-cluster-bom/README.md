# Exercise 2.2 — Small-cluster servers, rack units, ports, and links

**Difficulty:** ★★ · **Tier:** L1 · **Type:** outline-mandated · **Kind:** computed · **Points:** 20

## Prompt

<!-- prompt:start -->
*(Outline-mandated: estimate the number of GPU servers, rack units, network ports, and fabric links
for a small cluster using stated assumptions.)*

Halcyon wants a 128-GPU cluster, **ORION-128**, from HX8 nodes, in an older hall. Assumptions
`[ILLUSTRATIVE]`:

- HX8 as in Chapter 2: 8 GPUs, 8U, 10.2 kW maximum; rack auxiliary load 0.2 kW.
- Rack circuits: 415 V three-phase, **32 A**, two circuits per side, 2N A/B; derate 0.80; power factor
  0.95; transient margin 10 %. 48U racks.
- Backend: rail-optimized, 8 rails, 400 Gb/s, 64-port leaves, 1:1; spines of 64 ports; every leaf has
  the same number of uplinks to every spine.
- Frontend: 2 × 200 Gb/s per node. OOB: one 1 GbE port per node BMC, per switch (backend and two
  frontend leaves), per storage server (4), and per rack PDU (4 PDUs per GPU rack).

Tasks:

1. How many nodes fit per GPU rack electrically? How many GPU racks are needed, and how many rack
   units do nodes occupy per full rack?
2. How many rail leaves and spines are required? How many host-to-leaf and leaf-to-spine links? How
   many switch ports are used and how many are left unused on the leaves?
3. How many single-port 400G transceivers are needed if every link is optical?
4. What is the bisection bandwidth per direction?
5. How many frontend node ports and OOB ports are required?
6. State one assumption you would most want to verify before ordering, and why.

**Evidence required:** a BOM table (item, quantity, formula); the per-side power calculation; a
one-line justification for the spine count.
<!-- prompt:end -->

## What to submit

Put every deliverable in [`outputs/`](outputs/):

- `outputs/bom.md`: BOM table (item, quantity, formula), per-side power calculation and the spine-count justification

Command to run (from this folder):

```bash
python outputs/model.py --out outputs/   # if you script the BOM
```

Label every number you produce (`[MODELED]`, `[ILLUSTRATIVE]`, `[MEASURED]` and so on) and show formula, substitution and result with units.
