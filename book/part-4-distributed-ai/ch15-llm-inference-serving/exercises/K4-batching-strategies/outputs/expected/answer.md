# K4 — Static, dynamic and continuous batching: worked solution

**Strategies (Section 15.4):**

- **Static batching:** a fixed batch of requests is formed and run until the *longest* finishes. Slots of
  requests that finish early sit idle, and new arrivals wait for the whole batch.
- **Dynamic batching:** the server forms a batch when it reaches a size limit or a timeout expires, which
  is better for arrival variability. The batch still runs to completion, so the early-finisher waste
  remains for generation.
- **Continuous (iteration-level) batching** (Orca): the scheduler admits and retires sequences at *every
  decode iteration*. A finished sequence's slot is refilled on the next step, so the batch stays full and
  throughput is high.

**Why continuous batching creates prefill–decode interference.** A newly admitted request must be
prefilled before it can decode, and in a shared engine that prefill runs as (part of) an iteration. During
that iteration the running sequences get either **no token** (whole-prompt prefill: the iteration takes
t_p, about 90–180 ms for 2–4k prompts) or a **slower token** (chunked prefill: each iteration carries a
chunk, for example 512 tokens ≈ 22.6 ms on TP = 4 FP8, on top of the decode work). Interference grows with
the prefill share ρ_prefill = λ_r × t_p. Mean TPOT is inflated by 1/(1 − ρ), and the worst ITL is
t_d + t_p (Section 15.7, case W2).

Mitigations: chunked prefill (bounded stall), prefill priority limits, or disaggregation (separate prefill
and decode pools, Section 15.9).
