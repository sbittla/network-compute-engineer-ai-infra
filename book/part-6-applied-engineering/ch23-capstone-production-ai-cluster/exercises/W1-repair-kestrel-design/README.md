# W1 — Repairing the Kestrel design (★★, L1)

Worked problem · difficulty ★★ · tier L1 · kind `computed` · [exercise index](../README.md)

<!-- prompt:start -->
**W1 ★★ L1 — Repairing the Kestrel design.** Team Kestrel's bundle lists 34 HX8 nodes, 8 GPUs per
node, `total_gpus: 256`, no declared spares, workload parallelism TP = 8, PP = 4, DP = 16, rail
leaves of radix 64 with 34 downlinks and 32 uplinks (8 per spine, 4 spines), a claimed "1:1"
subscription, 512 backend cables, and 8 GPU racks with a usable budget of 45 kW each. The team says
two nodes are spares that must stay cabled to the backend so a failed node can be swapped without
recabling.

1. Fix the GPU accounting and the parallelism so that the design is internally consistent.
2. Show the leaf port arithmetic, then propose a leaf configuration that keeps both spares cabled,
   uses an equal number of uplinks to each spine, and fits radix 64. State the resulting
   oversubscription with and without the spares active, the spine port usage, and the backend cable
   count.
3. How many racks does a 34-node design need at 45 kW per rack? What are the options if the row has
   only 8 racks?

*Evidence required:* every formula with substituted values; final numbers with units.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Run:

```bash
python solve.py --out outputs   # optional: script your arithmetic
```
