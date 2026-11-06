# 2.1.6 — `SW Power Cap: Active` during a dense GEMM

Source: manuscript Section 2.6 ("Power capping", "Throttling: how power and heat show up as clocks").
Field names `[VENDOR-SPEC, 2026-10]`.

**Not a fault by itself.** A dense BF16 GEMM drives an H100-class GPU to its power limit. The power
controller then holds power at the limit by lowering clocks, and `nvidia-smi -q -d PERFORMANCE` reports
`SW Power Cap: Active`. That is the controller doing its job at the configured 700 W.

**It becomes a fault when:**

1. The limit is lower than intended. Check `nvidia-smi -q -d POWER` and compare `Current Power Limit`
   with `Default Power Limit` (and `Requested`/`Enforced` where shown). A leftover 450 W cap from a test
   or a feed-loss policy that never reverted is a configuration fault.
2. Only some GPUs in a job are capped, or capped GPUs run at clocks well below their peers (compare
   `clocks.sm` across the job's GPUs). In a synchronous job those GPUs become stragglers.
3. It coincides with `HW Slowdown` or `HW Power Brake Slowdown`, which indicate a platform-level power
   event (for example a PSU or feed problem, Exercise 2.7), not the normal software cap.
