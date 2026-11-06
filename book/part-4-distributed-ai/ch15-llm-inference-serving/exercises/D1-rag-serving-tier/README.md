# D1 — RAG serving tier (★★★, L1)

Type: design-challenge · Kind: computed

## Prompt

<!-- prompt:start -->
**D1. ★★★ L1 — RAG serving tier.** Design the serving tier for a retrieval-augmented assistant.
It must handle 20 req/s at peak with 8,192-token prompts (retrieved context) and 300-token
outputs. The SLOs — a declared variation from W-INFER's 800 ms / 50 ms targets — are TTFT p95 ≤ 1.5 s and TPOT p95 ≤ 40 ms. Use T-tp4-fp8 replicas, and include
the quadratic attention term in prefill.
Decide between a shared pool (with or without chunked prefill) and disaggregated serving. Size
the pools and choose a transport. Give the KV-transfer network budget, the QoS and isolation
design, and the failure behaviour (what happens when a decode replica dies). State three
measurements you would take at L2/L3 before committing.
*Evidence required:* a sizing table with ρ, TTFT, TPOT and batch per pool, the network budget in
Gb/s with the arithmetic, a transport decision with numbers, a failure table, and an explicit
MODELED/MEASURED labelling of every number.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) (W-INFER for serving questions).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare your method with the worked solution and marking scheme in the chapter's `solutions/exercises/D1-rag-serving-tier/` (instructor material in the full repository; removed from student releases).

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/design.md`

Optional: if you script the arithmetic, save the script as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
