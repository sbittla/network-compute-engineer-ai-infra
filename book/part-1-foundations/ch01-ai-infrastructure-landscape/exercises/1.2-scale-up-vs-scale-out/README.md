# Exercise 1.2 — Scale-up versus scale-out for two workloads

**Difficulty:** ★★ · **Tier:** L1 · **Type:** outline-mandated · **Kind:** computed · **Points:** 20

## Prompt

<!-- prompt:start -->
Two hypothetical workloads run on ORION. Profiles are per GPU per step `[ILLUSTRATIVE]`:

| Workload | GPUs | Compute | NVLink bytes sent | NIC bytes sent | Observed step |
|---|---|---|---|---|---|
| A: 70B decode, TP = 8, batch 32 | 8 (one node) | 0.56 TFLOP | 0.147 GB | 0 | 9.5 ms |
| B: MoE training, expert parallel across 8 nodes | 64 | 400 TFLOP | 40 GB | 30 GB | 1.5 s |

Workload A also reads 20.18 GB from HBM per GPU per step; B reads 500 GB.

1. Compute each workload's compute, memory, scale-up, and scale-out lower bounds.
2. State which resource dominates each workload and which network (scale-up or scale-out) carries
   the communication that matters.
3. For each, name two pieces of telemetry that would confirm your conclusion on real hardware and
   say what values you would expect.
4. For B, propose one placement change that would shift communication from scale-out to scale-up and
   state its limit on ORION.

**Evidence required:** a table of the eight lower bounds with formula and units; the dominant
resource per workload with ceiling fraction; named metrics with expected direction/magnitude; one
placement proposal with its constraint.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare your method with the worked solution and marking scheme in the chapter's `solutions/exercises/1.2-scale-up-vs-scale-out/` (instructor material in the full repository; removed from student releases).

## What to submit

Put every deliverable in [`outputs/`](outputs/):

- `outputs/answer.md`: the eight lower bounds table, dominant resources, telemetry and placement proposal

Optional: if you script the arithmetic, save the script as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```

Label every number you produce (`[MODELED]`, `[ILLUSTRATIVE]`, `[MEASURED]` and so on) and show formula, substitution and result with units.
