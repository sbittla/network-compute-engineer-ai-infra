# 14.9 result `[MODELED]`

(a) 16,000 img/s and 1.92 GB/s per node; 256,000 img/s and 30.7 GB/s cluster
(b) in flight 76.8/node; opens needed 256,000/s vs 50,000/s -> max 3,125 img/s/node -> metadata-bound
(c) 4,474 img/shard; 3.6 opens/s/node; PFS share 19 %; 114 req/s, 1.4 in flight -> bandwidth-bound, far from limit
(d) dataset 4.8 TB fits in 30.7 TB; staging 76.8 TB at 160 GB/s = 480 s
(e) repack into shards; confirm with meta_time_share >= 0.5 and mean_read_bytes < 1 MiB
