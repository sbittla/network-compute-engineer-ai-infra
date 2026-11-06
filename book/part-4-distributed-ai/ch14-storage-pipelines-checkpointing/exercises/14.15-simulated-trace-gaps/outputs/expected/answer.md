# 14.15 — What the simulated trace does not capture: worked solution

The lab trace is `[SIMULATED]`, generated from independent latency distributions with planted anomalies.
A real parallel file system adds the following behaviours:

| Behaviour not captured | Effect on the real tail | Reason |
|---|---|---|
| MDS request queueing and RPC flow control (credits, max RPCs in flight) | **Worse**, burstier | When credits run out, clients stall in batches. Many workers' opens queue together, so tails cluster |
| Client page and metadata caching (dentry/inode, read cache) | **Better** for re-reads | A second epoch over the same files hits the client cache. Stat/open of cached entries avoids the MDS |
| Lock contention on shared files (extent/DLM locks) | **Worse** | Several clients writing one shared file serialize on lock callbacks, adding round trips |
| Server-side caching and readahead | **Better** for sequential reads | OSS readahead turns sequential shard reads into cache hits |
| Frontend network congestion (incast at clients, shared with other tenants) | **Worse** | Many OSSs answering one client at once overflow switch buffers and cause retransmissions |
| Correlated slowdowns across targets (RAID rebuild, failover, a slow OSS) | **Worse** for affected steps | One slow target delays every read striped over it, so tails are correlated across ranks, not independent |

Any four of these suffice. The overall direction is that a real system's **p99.9 is usually worse and
more correlated** than the trace suggests, while its median for re-read data can be better. That is
why acceptance must be measured on the real system under realistic concurrency (Section 14.6), and why
the independence assumption in 14.7 is optimistic for some steps.
