# Capstone D — Exemplar Summary (abridged, distinction level)

INSTRUCTOR ONLY. Written as the learner would write it. Capacity figures are `[MODELED]` and latency and
throughput are `[SIMULATED]` (5 independent 15-minute traces; steady-state window excludes 60 s at each
end), unless marked otherwise.

## 1. Recommendation

Serve chat traffic on **FP8, TP = 4, two replicas per HX8 node, chunked prefill with a 2,048-token
budget**, conditional on the FP8 offline quality evaluation passing. Route the `rag-long` tenant to a
**separate replica pool** with its own TTFT SLO.

- **Chat-only:** a node meets every SLO on all 5 seeds at 3.0× the trace rate: TTFT p95 0.27 s
  [0.25–0.28], TPOT p95 26 ms, ITL p99 78 ms. The cost is **$0.27 per M total tokens**, against $0.60 at
  1.0×.
- **Mixed traffic:** the same node passes on only 4 of 5 seeds at 1.0× and fails at 1.25×. The
  long-context prompts, not the fleet size, are the problem.

## 2. Capacity model

KV per token = 2 × 80 × 8 × 128 × 2 B = 327,680 B (320 KiB). The vendor sheet's "320 KB" understates
it by 2.4 %.

- **TP8 BF16:** 404 GB of KV, which is 1,232,910 tokens.
- **TP4 FP8:** 202 GB, which is 616,455 tokens per replica.
- **Prefill:** a 2,048-token chunk costs ≈ 72 ms of linear compute against ≈ 7.5 ms of weight reads
  (compute-bound). For a 32k prompt, causal attention (2·L·d·n² ≈ 1.34 × 10¹⁵ FLOP for n = 32,000; 1.41 × 10¹⁵ for n = 32,768) adds ≈ 30 % to the
  linear 4.4 × 10¹⁵. A RAG prefill therefore takes ≈ 1.4 s on TP4 FP8.
- **Decode:** a 64 × 2k decode reads 17.5 GB of weights plus 5.2 GB of KV per GPU, ≈ 9.7 ms
  (memory-bound), plus 3 ms overhead.

## 3. Findings (median [min–max] over 5 seeds)

| Finding | Evidence |
|---|---|
| Long prompts cause head-of-line blocking | c1 at 1.0×: TTFT p95 1.39 s [1.25–1.53] on mixed traffic, but 0.40 s chat-only even at 2.0× |
| Mean TPOT hides token stalls | c2 chat-only at 2.0×: TPOT p95 41 ms (passes) but ITL p99 241 ms [221–257] (fails). c1's 2,048-token mixed iterations (≈ 78 ms) put its mixed-traffic ITL p99 at ≈ 103 ms |
| The highest throughput is an unstable system | c1 at 2.0× mixed reaches 2,784 tok/s per node while TTFT grows 0.029 s per second of arrival, so the queue never drains. We report it as unstable and quote no p95 or cost |
| One trace would have misled us | c3 at 1.0× mixed passes on 4 seeds and fails on one (TTFT p95 0.86 s) |
| Capping context "meets" latency by failing requests | c4: TTFT p95 0.19 s, but 2.1 % rejected, a ≈ 21× burn of a 99.9 % budget |

## 4. SLOs and rollout

- **TTFT:** measured at the gateway, accept to first streamed byte, for prompts ≤ 2,048 tokens. Of the
  0.8 s, 30 ms is budgeted to the frontend `[ILLUSTRATIVE]`, so the engine target is 0.77 s.
- **TPOT and ITL:** TPOT (per-request mean) p95 ≤ 50 ms and ITL (per-token gaps) p99 ≤ 100 ms
  `[ILLUSTRATIVE]`.
- **Long-context tenant:** TTFT p95 ≤ 5 s, a product decision recorded as an assumption.
- **Error budget and paging:** the 30-day budget is 43.2 min. Paging is on burn ≥ 14.4 over 1 h.
- **Rollout:** shadow → 1-replica canary for 30 min → 25 % → 100 %. `rollback_decision` gates on SLO
  breach (including ITL), a > 10 % regression or fast burn. It would have stopped both c2 (ITL) and c4
  (burn).

## 5. Fleet and cost (example forecast: 40 chat req/s peak, 0.8 rag req/s)

- **Chat:** chat traffic at 1.0× is ≈ 4.9 req/s per node. With 3.0× verified, 40 / 14.7 ≈ 2.7, which
  rounds to 3 nodes, plus 1 for failure and deploy surge: 4 nodes.
- **RAG:** 0.8 req/s × ≈ 1.4 s of prefill ≈ 1.1 replicas of prefill capacity, so one node (two TP4
  replicas), to be confirmed by simulating that pool against its 5 s SLO.
- **Total:** 5 nodes = 40 GPUs ≈ $88/h, or ≈ $135/h after dividing by 0.65 utilization `[MODELED,
  ILLUSTRATIVE prices]`.

## 6. Failure and security highlights

- **GPU loss:** losing one GPU (for example an uncontained ECC error, Xid 95) takes down its whole TP
  group. With TP4 that is half a node, a reliability argument for c3.
- **KV exhaustion:** it shows up as preemptions, which are alerted on before TTFT degrades.
- **Oversized requests:** requests larger than a replica's KV capacity are rejected at admission rather
  than queued forever.
- **Tenancy and data:** tenants never share prefix or KV caches, and prompt logging is opt-in and
  redacted.

## 7. Next steps

1. **P0:** an L2 load test of c3 versus c1 on one node with the same trace shape, to calibrate the
   roofline efficiencies (A-01, A-02) and the measured ITL tail.
2. **P0:** the FP8 quality evaluation.
3. **P1:** evaluate disaggregated serving for the RAG pool (Capstone H).
