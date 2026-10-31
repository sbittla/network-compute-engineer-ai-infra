# K5 — Goodput: worked solution

**Definitions (Section 15.7).**

1. **DistServe goodput:** the *maximum request rate* a system can sustain such that a target fraction
   (for example 90 %) of requests meet **both** the TTFT and TPOT SLOs. It is a capacity number for a
   configuration.
2. **Operational goodput on a trace:** SLO-meeting requests per second, that is the requests with
   TTFT ≤ SLO and TPOT ≤ SLO, divided by the trace duration. The lab's `slo_report` computes it.

**Why goodput can fall while throughput rises.** Throughput counts all completed work. Goodput counts only
work delivered within the SLOs. Raising the concurrency cap on a decode replica raises batch size, which
raises tokens/s (the decode step amortizes the weight read over more sequences). It also lengthens every
step. Scenario `[MODELED]`: on T-tp4-fp8 at W-INFER's 2k prompts (average context 2,176 tokens, so 278
sequences fit in KV), raising the cap from 48 to 256 concurrent sequences moves the decode step from
14.1 ms to 29.9 ms (10.46 ms + B × 0.076 ms). With prefill stalls (÷ (1 − ρ), ρ ≈ 0.45) TPOT reaches
≈ 55 ms. Tokens/s per replica rises (≈ 3,400 → 8,600), but every request's TPOT now exceeds the 50 ms
SLO, so goodput drops toward zero although throughput is higher than ever. Queue-driven collapse behaves the same way: during a burst all requests complete eventually, but
TTFT p95 of 28.8 s means almost none count.

**From the lab trace `[SIMULATED]`:** throughput 7.57 req/s, goodput 3.69 req/s. Half the completed
requests missed an SLO, mostly in the burst and storm episodes.

**Common wrong answer.** Calling the throughput of completed requests "goodput".
