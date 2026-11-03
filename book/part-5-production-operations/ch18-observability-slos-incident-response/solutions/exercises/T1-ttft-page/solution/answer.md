# T1 — The TTFT page on chat-70b

| Rank | Hypothesis | Evidence for / against (lines quoted) | Verdict |
|---|---|---|---|
| 1 | DEP-44 (rev 44) doubled vLLM's CPU swap area: `--swap-space` is GiB *per GPU*, so 8 GiB × 8 GPUs = 64 GiB of pinned host memory (was 32 GiB). With the process baseline that exceeds the pod's 64 GiB memory limit, so the kernel cgroup OOM killer ends the container; the rolling update stalls with replica 7 down (1/8 of capacity) and the other replicas queue | `19:52 DEP-44 ... --swap-space 4 → 8 GiB` precedes restarts `0 → 4 between 19:55 and 20:04` and the TTFT rise from 20:00; `Reason: OOMKilled Exit Code: 137` (137 = SIGKILL from the cgroup, i.e. *host* memory); `working_set 63.9 GiB of 64 GiB limit`; `rev 44: 1 of 8 updated, not Ready`; `num_requests_waiting 35-48` on replicas 0–6; replica 7 `series absent since 19:58` | **Root cause** (confirm by rollback) |
| 2 | Traffic surge | 3,050 → 3,120/min = +2.3 %, normal evening growth; cannot explain a 3× TTFT | Rejected |
| 3 | GPU memory (HBM) exhaustion from 32k context | `FB_USED 73-74 GiB of 79.6 GiB` on *all* replicas, unchanged since 19:00: vLLM pre-allocates `--gpu-memory-utilization` (≈ 0.92 × 79.6 ≈ 73 GiB) for weights and KV cache at start-up, so near-full HBM is its normal state. A CUDA OOM raises `torch.OutOfMemoryError` in the process and exits with code 1, not an `OOMKilled` 137 | Rejected (distractor) |
| 4 | GPU hardware fault | `GPU Xid: none`; the exit is a host-memory kill, not a device error | Rejected |
| 5 | Fabric or storage | `fabric: normal; storage: normal`; TP = 8 serving inside one HX8 does not use the backend fabric per request | Rejected |
| 6 | Bad model/code path raising errors | 5xx 0.01 % (normal); the alert is latency, not availability | Rejected |

**Why TPOT is flat while TTFT explodes.** TTFT includes *queueing* before prefill: with replica 7 down
and the other seven saturated, new requests wait in the scheduler queue (`num_requests_waiting`
35–48), so time to first token rises from 0.62 s to 1.9 s. TPOT is measured per output token of
requests that are already running; they decode at the normal per-token rate (38 ms), so TPOT does not
move. Only replica 7 has crashed because it is the only rev-44 pod: the rolling update waits for it to
become Ready. Forcing the rollout on would OOM-kill the other seven as well.

**Mitigation first:** `kubectl rollout undo deploy/chat-70b` to rev 43 (the change precedes the
symptom; rollback is the safest and fastest action, no diagnosis needed to justify it). Re-ship 32k
context later with the swap area unchanged or the memory limit raised to fit swap × TP + baseline.

**Validation criteria:** no new restarts for 30 min; working set below 80 % of the limit; `num_requests_waiting` < 5 on all replicas; TTFT
p95 < 0.8 s (the SLO threshold); 5-minute burn < 1 and `ChatTTFTFastBurn` resolves; replica 7 series
present again.

**Follow-up (postmortem actions):** a deploy-time check that host memory (swap area × TP + process
baseline) fits the pod limit; a canary gate that fails on restarts, not only on latency; KV-cache and
context sizing per Chapter 15. `--swap-space` semantics are `[VENDOR-SPEC, 2026-10]`; verify per vLLM
release. The scenario states a V0-engine release; in current V1 releases the flag may be deprecated
or have no effect, but any host-side memory increase gives the same `OOMKilled`/137 signature.
