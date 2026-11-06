# W1 — Repairing the Kestrel design (★★, L1)

Worked problem · difficulty ★★ · tier L1 · kind `computed` · [exercise index](../README.md)

<!-- prompt:start -->
**W1 ★★ L1 — Repairing the Kestrel design.** Team Kestrel's bundle lists 34 HX8 nodes, 8 GPUs per
node, `total_gpus: 256`, no declared spares, workload parallelism TP = 8, PP = 4, DP = 16, rail
leaves of radix 64 with 34 downlinks and 32 uplinks (8 per spine, 4 spines), a claimed "1:1"
subscription, 512 backend cables, and 8 GPU racks with a planned budget of 45 kW each (a 50 kW rack
limit less Chapter 21's 10 % transient margin). The team says
two nodes are spares that must stay cabled to the backend so a failed node can be swapped without
recabling.

1. Fix the GPU accounting and the parallelism so that the design is internally consistent.
2. Show the leaf port arithmetic, then propose a leaf configuration that keeps both spares cabled,
   uses an equal number of uplinks to each spine, and fits radix 64. State the resulting
   oversubscription with and without the spares active, the spine port usage, and the backend cable
   count.
3. How many racks does a 34-node design need at the 45 kW planned budget? What are the options if the row has
   only 8 racks?

*Evidence required:* every formula with substituted values; final numbers with units.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare your method with the worked solution and marking scheme in the chapter's `solutions/exercises/W1-repair-kestrel-design/` (instructor material in the full repository; removed from student releases).

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Optional: if you script the arithmetic, save the script as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```
