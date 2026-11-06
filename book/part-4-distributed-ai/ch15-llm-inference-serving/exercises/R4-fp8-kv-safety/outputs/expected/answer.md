# R4 — Evidence for FP8 KV safety: worked solution

A memory saving (2× KV capacity, W1) is a benefit, not evidence of safety. Before enabling FP8 KV for the
long-context tenant:

1. **Offline quality evaluation at real context length.** Run the tenant's own task suite (or the closest
   public long-context benchmarks: retrieval, multi-document QA, summarization) at 8–12k tokens with BF16
   KV and FP8 KV, same weights, same decoding settings, enough samples for a confidence interval.
   *Acceptance:* the task-metric difference stays within the pre-agreed tolerance (for example ≤ 0.5
   points absolute, or not statistically worse at 95 %), with no regression on the longest-context
   bucket. Errors accumulate with context, so 2k results do not transfer.
2. **Canary with per-tenant quality signals.** Route a small share (for example 5 %) of the tenant's
   traffic to FP8-KV replicas for a defined period. *Acceptance:* user-facing quality signals (thumbs-down
   rate, regeneration rate, task success, or LLM-judge pairwise preference on sampled outputs) are not
   worse than the BF16 control beyond the stated threshold, and latency improves as modeled.
3. **Engine and model support.** Confirm that the serving engine version supports FP8 KV for this
   architecture with proper per-tensor or per-head scaling (calibrated scales rather than unit scales)
   and that attention kernels for that path are validated `[VENDOR-SPEC, 2026-10]`. *Acceptance:* the
   configuration is listed as supported, the calibration step was run on representative data, and a smoke
   test matches BF16 logits within a stated tolerance on fixed prompts.

Also useful: a rollback plan, a per-tenant opt-out, and a monitored quality alert after full rollout.
