# Exercise 4.14 — p99 tripled after a release

★★★ · Tier L1 · troubleshooting case · kind: `written`

<!-- prompt:start -->
**4.14** ★★★ L1 — An inference service on one ORION GPU meets its p50 latency SLO but p99 latency
has tripled since a release. GPU-Util is 70–80 %. A 10-second nsys capture gives (abridged,
`[ILLUSTRATIVE]`):

```text
 Time (%)  Total Time (ns)  Num Calls   Avg (ns)     Name
     48.0    2,520,114,800      2,100   1,200,054    cudaFree
     21.5    1,128,744,120        420   2,687,486    cudaMalloc
     19.9    1,044,812,000    452,113       2,311    cudaLaunchKernel
      6.1      320,251,000      2,100     152,500    cudaStreamSynchronize
```

The GPU row shows a 1–4 ms idle gap after almost every request, each beginning when a `cudaFree` call
starts. The release notes include "free GPU memory between requests to reduce fragmentation".
Rank three hypotheses, name the discriminating evidence for each, identify the root cause, propose a safe
fix and a validation plan.
*Evidence required:* ranked hypotheses, evidence mapping, root cause, fix with rollout, validation with
percentiles.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the Table 4.1 (H100-SXM-class) values.
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the worked answer and marking scheme in the chapter's `solutions/exercises/4.14-p99-allocator-churn/` (instructor material in the full repository; removed from student releases).

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — your answer, written to the evidence requirement above
