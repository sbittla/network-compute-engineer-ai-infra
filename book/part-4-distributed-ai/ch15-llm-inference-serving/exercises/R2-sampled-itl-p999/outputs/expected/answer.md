# R2 — What a 5 % ITL sample can show: worked solution

**Sample size `[SIMULATED]`.** The trace has about 4,540 requests (7.57 req/s × 600 s). A 5 % sample is
≈ 227 requests and, at about 316 gaps each, ≈ 72k inter-token gaps. The p99.9 of 72k gaps rests on the
top ≈ 72 values.

**Why that is weaker than it looks.** The 72 extreme gaps are not 72 independent observations. A single
stall (a 180 ms prefill admitted into the batch, a preemption) hits *every* co-scheduled sequence in the
same iteration, and a slow replica produces long gaps throughout each of its requests. Gaps within one
request, and across requests on one replica at one moment, are correlated. The effective sample size for
the tail is roughly the number of distinct *stall events* in the sample, perhaps tens, not 72k.

**What can be concluded.**

- p50 and p99 trends (for example baseline ITL p99 216 ms vs burst 444 ms) are reliable enough to compare
  segments.
- p99.9 shows that rare multi-hundred-ms stalls exist, but its value can move by a large factor depending on
  which few requests were sampled. It must not be used for SLO compliance or for comparing two
  configurations.

**Better instruments.** Record **per-request max ITL** (and count of gaps > threshold) for 100 % of
requests: one number per request with no sampling bias in the tail. Or raise the gap sampling rate during
investigation, or log stall events (prefill admissions, preemptions) with timestamps, so tails can be
attributed to causes rather than counted.
