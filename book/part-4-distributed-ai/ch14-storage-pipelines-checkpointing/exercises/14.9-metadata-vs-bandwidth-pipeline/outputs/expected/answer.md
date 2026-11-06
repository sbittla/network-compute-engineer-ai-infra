# 14.9 — Metadata-bound versus bandwidth-bound pipeline: worked solution

Inputs are from the prompt `[ILLUSTRATIVE]`. Results are `[MODELED]`. HX8 has 8 GPUs and 8 × 3.84 TB
NVMe = 30.7 TB raw per node (`docs/REFERENCE_CLUSTER.md`). Method: Section 14.5.

**(a) Demand.**

```text
per node:  8 GPUs × 2,000 images/s = 16,000 images/s;  × 120 KB = 1.92 GB/s
cluster:   16 nodes × 16,000       = 256,000 images/s; × 120 KB = 30.7 GB/s
```

**(b) One file per image.** Per-sample latency = open 4.0 + read 0.6 + close 0.2 = 4.8 ms.

```text
in flight per node (Little)  = 16,000 /s × 0.0048 s = 76.8 requests
cluster open rate needed     = 256,000 /s  vs  50,000 /s available
max images/s per node        = 50,000 / 16 = 3,125  (19.5 % of 16,000)
```

**Metadata-bound.** Adding loader workers raises in-flight requests but cannot raise the MDS ceiling.

**(c) 512 MiB shards, 16 MiB requests of 12 ms.**

```text
images per shard        = 536,870,912 B / 120,000 B ≈ 4,474
opens per node          = 16,000 / 4,474 ≈ 3.6 /s   (57 /s cluster-wide, 0.1 % of the MDS)
PFS bandwidth share     = 30.7 / 160 = 19 %
requests per node       = 1.92e9 B/s / 16,777,216 B = 114 /s
in flight per node      = 114 /s × 0.012 s = 1.4
```

**Bandwidth-bound in character but far from any limit:** a 5× bandwidth margin and trivially few opens.

**(d) Local staging.** Dataset = 40 × 10⁶ × 120 KB = **4.8 TB**. It fits in 30.7 TB per node, leaving
room for checkpoint staging. A full copy on all 16 nodes at once moves 16 × 4.8 = 76.8 TB from the PFS:
76.8 TB / 160 GB/s = **480 s (8 min)**, 10 GB/s per node (well under the 50 GB/s frontend).
Partition-aware caching, where each node caches only its shards, cuts this 16×.

**(e) Recommendation.** Repack into shards (WebDataset/MDS-style tar shards). This removes the metadata
bottleneck with 5× bandwidth headroom. Optionally add local staging to decouple from other tenants'
PFS load. Confirm the diagnosis on the current pipeline with the lab's window metrics:
`meta_time_share` ≥ 0.5 and `mean_read_bytes` < 1 MiB (metadata class), and MDS ops/s on its plateau
while OST throughput stays low.

**Common wrong answer.** "Add more data-loader workers." That raises opens/s demand on an MDS that is
already the bottleneck.
