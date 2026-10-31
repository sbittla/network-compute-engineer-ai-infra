# 12.9 — Buckets and the alpha-beta model (n = 64, α = 47 µs, B = 346 GB/s busbw)

Model (Section 12.3): t(S) = α + factor × S / B, factor = 2(n − 1)/n = 2 × 63/64 = 1.96875. MB = 10⁶ B.
All values `[MODELED]`.

**(a) Times**

```text
4 MB:   47 + 1.96875 × 4e6 / 346e9 s   = 47 + 22.8    = 69.8 µs
25 MB:  47 + 1.96875 × 25e6 / 346e9 s  = 47 + 142.3   = 189.3 µs
256 MB: 47 + 1.96875 × 256e6 / 346e9 s = 47 + 1,456.6 = 1,503.6 µs
```

**(b) n½** — the size at which the bandwidth term equals α (half of peak busbw is achieved):

```text
n½ = α × B / factor = 47e−6 s × 346e9 B/s / 1.96875 = 8.26 MB
```

So a 4 MB bucket runs at 22.8/69.8 = 33 % of plateau and a 25 MB bucket at 75 %.

**(c) Reducing 4.375 GB of gradients**

```text
buckets:   4.375e9 / 25e6 = 175 buckets × 189.3 µs              = 33.1 ms
one shot:  47 µs + 1.96875 × 4.375e9 / 346e9 s = 47 + 24,894 µs = 24.9 ms
difference 33.1 − 24.9 = 8.2 ms ≈ 174 extra α payments × 47 µs = 8.18 ms
```

The bandwidth terms are identical (same total bytes); bucketing pays the fixed α once per bucket.

**Why buckets still win in practice.** DDP launches each bucket's all-reduce as soon as its gradients
are ready, overlapping it with the rest of backward; only the last bucket(s) are exposed. One big
message would have to wait for the whole backward pass and then run fully exposed. Buckets well above
n½ (25 MB ≈ 3 × n½) keep the α tax modest while preserving overlap.

**Common mistakes.** Using algbw instead of busbw with the factor; forgetting the factor (gives
11.6 µs instead of 22.8 µs at 4 MB); computing n½ as α × B.
