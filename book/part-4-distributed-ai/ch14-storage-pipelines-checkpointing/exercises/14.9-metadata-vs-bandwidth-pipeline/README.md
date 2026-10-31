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

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Run:

```bash
python solution/solve.py --out outputs
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
