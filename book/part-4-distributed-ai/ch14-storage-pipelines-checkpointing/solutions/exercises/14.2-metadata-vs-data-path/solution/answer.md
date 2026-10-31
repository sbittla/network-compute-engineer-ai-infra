# 14.2 — Metadata path versus data path: worked solution

**RPC sequence for one file in a Lustre-class PFS (Section 14.4):**

```text
1. open("/pfs/data/shard_0042")  client → MDS (metadata server, serving the MDT)
      MDS: path lookup, permission check, open state
      reply: file LAYOUT = stripe count, stripe size, list of OSTs + object IDs
2. read(fd, off, len)            client → OSS(s) holding the OSTs for that byte range, directly
      client computes OST = (off / stripe_size) mod stripe_count from the layout
      (a large read fans out to several OSSs in parallel)
3. close(fd)                     client → MDS: release open state, update attributes (size, times)
```

**What the client gets at open time.** The **layout**: which object storage targets hold the file and
how the bytes are distributed across them. With it, every subsequent `read()`/`write()` goes straight
to the OSSs without involving the MDS. That is why the data path scales with the number of OSSs while
the metadata path is limited by the MDS.

**Stripe count and stripe size.**

- *Stripe count:* how many OSTs a file is spread over. More stripes give one file more aggregate
  bandwidth.
- *Stripe size:* how many bytes go to one OST before moving to the next, typically 1–16 MiB. It sets
  the request granularity per server and how evenly a single large I/O spreads.

**Where wider striping does not help:**

- *Many clients each with their own file* (a checkpoint with one shard per rank, 256 writers). The
  file count already spreads load across all OSTs. Extra stripes per file add objects, extent locks and
  per-file overhead, and can create lock contention.
- *Small files* smaller than one stripe. All bytes land on one OST regardless of stripe count, and the
  cost is the `open` on the MDS (Section 14.5, metadata-bound pipelines).

**Common wrong answer.** Saying that `read()` goes through the MDS.
