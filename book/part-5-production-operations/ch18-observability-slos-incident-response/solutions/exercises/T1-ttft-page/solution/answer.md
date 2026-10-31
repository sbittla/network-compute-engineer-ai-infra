# T1 — The TTFT page on chat-70b

| Rank | Hypothesis | Evidence for / against (lines quoted) | Verdict |
|---|---|---|---|
| 1 | DEP-44 (32k context, rev 44) made replica 7 exceed GPU memory; its crashloop removed 1/8 of capacity and the other replicas queue | `19:52 DEP-44 ... raise max context length to 32k` precedes restarts `3 → 6 between 19:55 and 20:04` and the TTFT rise from 20:00; `Reason: OOMKilled Exit Code: 137`; `FB_USED 79.1 GiB of 79.6 GiB`; `num_requests_waiting 35-48` on replicas 0–6; replica 7 `series absent since 19:58` | **Root cause** (confirm by rollback) |
| 2 | Traffic surge | 3,050 → 3,120/min = +2.3 %, normal evening growth; cannot explain a 3× TTFT | Rejected |
| 3 | GPU hardware fault | `GPU Xid: none`; exit 137 is a kill on a memory limit, not a device error | Rejected |
| 4 | Fabric or storage | `fabric: normal; storage: normal`; TP = 8 serving inside one HX8 does not use the backend fabric per request | Rejected |
| 5 | Bad model/code path raising errors | 5xx 0.01 % (normal); the alert is latency, not availability | Rejected |

**Why TPOT is flat while TTFT explodes.** TTFT includes *queueing* before prefill: with replica 7 down
and the other seven saturated, new requests wait in the scheduler queue (`num_requests_waiting`
35–48), so time to first token rises from 0.62 s to 1.9 s. TPOT is measured per output token of
requests that are already running; they decode at the normal per-token rate (38 ms), so TPOT does not
move. Only replica 7 has crashed so far, plausibly because it was first to receive a long
enterprise prompt; the others are at risk of the same OOM.

**Mitigation first:** roll back to rev 43 (the change precedes the symptom; rollback is the safest
and fastest action, no diagnosis needed to justify it). Optionally shed or route enterprise long-context
traffic away until the rollback completes.

**Validation criteria:** no new restarts for 30 min; `num_requests_waiting` < 5 on all replicas; TTFT
p95 < 0.8 s (the SLO threshold); 5-minute burn < 1 and `ChatTTFTFastBurn` resolves; replica 7 series
present again.

**Follow-up (postmortem actions):** capacity model for 32k context (KV cache and activation memory,
Chapter 15); CI check of memory headroom per maximum context; canary with long-prompt test traffic.
