# T1 · The TTFT page on chat-70b (★★★ · L1)

Type: troubleshooting · Kind: written · Points: 10

<!-- prompt:start -->
**T1 ★★★ L1 — The TTFT page.** At 20:05 `ChatTTFTFastBurn` pages for `chat-70b` (8 replicas, TP = 8,
one replica per HX8 node). Evidence `[ILLUSTRATIVE]`:

```text
20:00  TTFT p95 0.62 s → 20:04 1.9 s;  TPOT p95 flat at 38 ms;  5xx rate 0.01 % (normal)
20:00  request rate 3,050/min → 20:04 3,120/min (normal evening growth)
vllm:num_requests_waiting   replicas 0-6: 0-2 → 20:04: 35-48      replica 7: series absent since 19:58
kube_pod_container_status_restarts_total{pod="chat-70b-7"}  0 → 4 between 19:55 and 20:04
kubectl describe pod chat-70b-7:  Last State: Terminated  Reason: OOMKilled  Exit Code: 137
container_memory_working_set_bytes{pod="chat-70b-7"} (before each kill): 63.9 GiB of 64 GiB limit
DCGM_FI_DEV_FB_USED replicas 0-7: 73-74 GiB of 79.6 GiB per GPU (unchanged since 19:00)
kubectl rollout status deploy/chat-70b:  rev 44: 1 of 8 updated (chat-70b-7), not Ready
events: 19:52 DEP-44 "chat-70b: max context 32k for enterprise tier; --swap-space 4 → 8 GiB" (rev 44)
service: vLLM release running the V0 engine (--swap-space = CPU swap GiB per GPU)
fabric: normal; storage: normal; GPU Xid: none
```

Walk the diagnostic loop: rank hypotheses, name the discriminating evidence for each, state the root
cause, the mitigation you would take first, and how you would validate. Explain why TPOT is flat while
TTFT explodes.
*Evidence required:* ranked hypothesis table; root cause tied to specific lines above; mitigation +
validation criteria; the TTFT/TPOT explanation.
<!-- prompt:end -->

## What to submit

Write your answer in `outputs/answer.md`. Cover every item in the "Evidence required" line, cite the
manuscript Section, table, metric, or lab data file you used, and label numbers with their evidence
class (`[MODELED]`, `[SIMULATED]`, `[ILLUSTRATIVE]`).
