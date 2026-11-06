# Marking scheme: T1 The TTFT page on chat-70b

Type troubleshooting · kind written · tier L1 · 10 points

**Evidence required:** Ranked hypothesis table; root cause tied to specific lines above; mitigation + validation criteria; the TTFT/TPOT explanation.

| Criterion | Points |
|---|---|
| Ranked hypotheses: DEP-44 swap-space increase -> host-memory OOM kill of the rev-44 pod first; HBM exhaustion (FB_USED is normal vLLM pre-allocation), surge, GPU fault, fabric/storage rejected | 3 |
| Evidence citations tied to the specific lines (19:52 DEP-44, OOMKilled 137, working set 63.9/64 GiB, rollout 1 of 8 not Ready, restarts 0 → 4, queue 35–48, series absent) | 3 |
| Mitigation (roll back to rev 43) with validation thresholds | 2 |
| TTFT includes queueing before prefill; TPOT is per-token decode of running requests, so it stays flat | 2 |
