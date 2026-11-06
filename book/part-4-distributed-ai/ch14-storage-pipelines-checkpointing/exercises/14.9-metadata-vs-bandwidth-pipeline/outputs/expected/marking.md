# Marking scheme: 14.9 Metadata-bound versus bandwidth-bound pipeline

Type worked-problem · kind computed · tier L1 · 10 points

**Evidence required:** all arithmetic; a classification of each option as metadata-bound or bandwidth-bound

| Criterion | Points |
|---|---|
| (a) 16,000 images/s and 1.92 GB/s per node; 256,000 images/s and 30.7 GB/s cluster | 2 |
| (b) 76.8 in flight per node; 256,000 opens/s vs 50,000; 3,125 images/s per node (19.5 %), metadata-bound | 3 |
| (c) ≈ 4,474 images per shard, ≈ 3.6 opens/s per node, 19 % of PFS, ≈ 1.4 requests in flight, bandwidth-bound with margin | 2 |
| (d) 4.8 TB fits on 30.7 TB NVMe; full staging 76.8 TB in 480 s | 2 |
| (e) Recommend shards (plus optional staging); confirm with meta_time_share and mean_read_bytes | 1 |
