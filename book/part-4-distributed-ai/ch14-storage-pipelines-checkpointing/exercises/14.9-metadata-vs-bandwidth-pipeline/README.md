# 14.9 — Metadata-bound versus bandwidth-bound pipeline (★★, L1)

Type: worked-problem · Kind: computed

## Prompt

<!-- prompt:start -->
**14.9 Metadata-bound versus bandwidth-bound pipeline** ★★ · L1 **(outline)**
A vision job on 16 HX8 nodes needs 2,000 images/s per GPU. The dataset is 40 million images averaging
120 KB. The PFS metadata service sustains ≈ 50,000 `open`/s for this job `[ILLUSTRATIVE]` and the PFS
reads 160 GB/s aggregate. Per sample: `open` 4.0 ms, `read` 0.6 ms, `close` 0.2 ms. Shard option:
512 MiB shards read in 16 MiB requests of 12 ms each.
(a) Required images/s and GB/s per node and cluster-wide. (b) For one file per image: requests in
flight per node, cluster `open` rate, and the maximum images/s per node the metadata service allows.
(c) For shards: opens per second per node, bandwidth share of the PFS, and requests in flight per
node. (d) Staging alternative: does the dataset fit on local NVMe, and how long does staging take if
all nodes stage at once? (e) Recommend, and say which lab metric would confirm your diagnosis on the
current pipeline. *Evidence required:* all arithmetic; a classification of each option as
metadata-bound or bandwidth-bound.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 14 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the W-TRAIN values.
- **Local NVMe for part (d):** each HX8 node has 8 × 3.84 TB U.2 NVMe, ≈ 30.7 TB raw per node (the Local NVMe row of the HX8 node table in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md)). Staging reads come from the PFS, so use the prompt's 160 GB/s aggregate for the all-nodes-at-once case.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Optional: if you script the arithmetic, save the script as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
