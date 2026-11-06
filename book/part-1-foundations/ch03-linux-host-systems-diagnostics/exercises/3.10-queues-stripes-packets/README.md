# Exercise 3.10 — Queues, stripes and packets

**Difficulty:** ★★ · **Tier:** L1 · **Type:** worked-problem · **Kind:** computed · **Points:** 10

## Prompt

<!-- prompt:start -->
Use the live `iostat` report in the `orion-n12` snapshot (`lab/data/snapshots/orion-n12.json`).
(a) Verify the `aqu-sz` of `nvme3n1` and of `md0` with Little's law.
(b) Compute `md0`'s delivered read throughput in MB/s (SI), from `r/s` and `rareq-sz`.
(c) The loader keeps about 41 requests of 512 KiB outstanding against `md0`. If `nvme3n1` behaved like
its siblings, so that array latency fell to about 0.25 ms, what throughput would the concurrency allow,
and what would then become the limit?
(d) Show that the snapshot's `%iowait` is consistent with the `vmstat b` value.
(e) Compute the frontend packet rate at 200 Gb/s for MTU 9000 and MTU 1500, and the ratio between them.
*Evidence required:* every formula with substituted values; one sentence of interpretation per part.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in [`outputs/`](outputs/):

- `outputs/answer.md`: your answer with the evidence the prompt requires

Optional: if you script the arithmetic, save the script as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```

Label every number (`[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`) and show formula, substitution and result with units. Quote raw snapshot lines where you rely on them.
