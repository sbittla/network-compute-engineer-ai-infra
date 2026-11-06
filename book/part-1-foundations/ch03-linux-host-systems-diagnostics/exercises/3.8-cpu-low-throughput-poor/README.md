# Exercise 3.8 — CPU utilization is low but throughput is poor

**Difficulty:** ★★ · **Tier:** L1 · **Type:** troubleshooting · **Kind:** computed · **Points:** 10

## Prompt

<!-- prompt:start -->
Snapshot `lab/data/snapshots/orion-n12.json` comes from a node running *W-MM*, an image–text
fine-tuning job. This is a variation on ORION's reference workloads: its training shards are read
from the node-local NVMe array `md0`, and each W-MM job runs on a single node (8 GPUs), so a slow node
slows only its own job. Samples per second on this node are about 40 % below its peers, which read
≈ 725 MB/s from their own `md0` in the same W-MM configuration `[ILLUSTRATIVE]`. The operator's note
says "CPU utilization is low".

1. From the snapshot alone, list every abnormal signal with its evidence: the section and the value.
2. Form **at least four hypotheses** that involve memory locality, I/O wait, interrupts, PCIe
   constraints or CPU frequency, and rank them by how well each explains a ≈ 40 % throughput loss.
3. For each hypothesis, give one **discriminating test** that you would run next on the live host (L2),
   and the result that would confirm or reject it.
4. State the most likely primary cause, the contributing factors, and the **order** of remediation.
   Each change must be safe (drained node, change process).
5. Define the measurement that would validate the fix: the metric, warm-up, repetitions and the
   statistic you would report.

*Evidence required:* a one-page report. It needs a signal table with section, value and baseline, a
ranked hypothesis table with tests, the root-cause statement, a remediation order and a validation
plan. Quote at least three raw lines from the snapshot.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in [`outputs/`](outputs/):

- `outputs/report.md`: one-page report: signal table, ranked hypotheses with tests, root cause, remediation order, validation plan, three quoted raw lines

Optional: if you script the arithmetic, save the script as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```

Label every number (`[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`) and show formula, substitution and result with units. Quote raw snapshot lines where you rely on them.
