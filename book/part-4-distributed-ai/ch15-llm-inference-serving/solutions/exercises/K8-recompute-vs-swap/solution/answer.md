# K8 — Recompute versus swap: worked solution

**Assumptions** `[ILLUSTRATIVE]`: TP = 2 replica with FP8 weights (70 GB) and BF16 KV (327,680 B/token),
prefill at 40 % MFU on 2 × 1,979 TFLOP/s FP8, PCIe Gen5 x16 at ≈ 50 GB/s achievable per GPU per
direction, and each GPU holding half the KV (TP shards KV heads).

**Recompute** (Section 15.5):

```text
prefill µs/token = 2 × 70e9 / (2 × 1,979e12 × 0.40) = 88.4 µs
recompute 10,000 tokens = 10,000 × 88.4 µs = 0.884 s
```

That is close to a second of prefill on the replica, during which every co-scheduled sequence stalls.
The quadratic attention term adds a little more at 10k tokens.

**Swap:**

```text
KV bytes = 10,000 × 327,680 B = 3.28 GB  → per GPU 1.64 GB
swap out = 1.64 GB / 50 GB/s = 32.8 ms;  swap in ≈ 32.8 ms   (≈ 66 ms round trip)
```

It also needs 3.28 GB of host memory per swapped sequence and competes with other PCIe traffic (NIC, data
loading).

**Comparison** `[MODELED]`: swap is ≈ 13× cheaper per event for long contexts, but it adds PCIe and
host-memory contention and is bounded by host memory when many sequences are swapped. Recompute needs no
host memory and is cheap for short contexts (a 500-token sequence costs 44 ms). Engines often pick by
context length. Any stated, reasonable PCIe assumption is acceptable.

**Common wrong answers.** Using BF16 TFLOP/s for an FP8 replica (doubles the recompute time). Moving the
full 3.28 GB over one GPU's link.
