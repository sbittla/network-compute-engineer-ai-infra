# Capstone H — Abridged Exemplar of a Distinction-Level Submission (INSTRUCTOR ONLY)

> Abridged model answer in the learner's voice. Suggested score ≈ 92/100. All results are
> `[MODELED]` (closed form) or `[SIMULATED]` (starter-kit simulator, seed-fixed trace); prices and
> two accelerator classes are `[ILLUSTRATIVE]`/hypothetical.

---

## 1. Recommendation

Serve W-INFER at 30 req/s as **5 prefill + 2 decode HX8 instances (56 GPUs, 7 of the 8 inference
nodes), with KV carried over rail-aligned RoCEv2 using GPUDirect RDMA in its own traffic class,
and with TTFT-predictive admission control.** Simulated on the burst trace:

| Metric `[SIMULATED]` | Result | SLO |
|---|---|---|
| TTFT p95 | 0.57 s | ≤ 0.8 s |
| TPOT p95 (per-request mean) | 17.6 ms | ≤ 50 ms |
| ITL p99 (per-token gap) | 18 ms | ≤ 100 ms |
| Second-token gap p95 | 30 ms | ≤ 100 ms (ITL budget) |
| Requests shed during the burst | 7.1 % | ≤ 10 % |
| Output throughput | 8,940 tokens/s | — |
| Cost | **$6.96 per million output tokens** | — |

**Co-finalist: fused chunked-prefill colocation on 7 nodes.** It is cheaper ($6.49 per million
tokens with 1,024-token chunks) and meets both TPOT (37.7 ms) and ITL p99 (58 ms). It fails TTFT
under the burst (p95 2.5 s), because the admission policy predicts queueing as if prefill ran on
dedicated instances.

**What would flip the decision:** a chunk-aware admission policy that brings colocated TTFT p95 to
≤ 0.8 s under the burst while keeping ITL p99 ≤ 100 ms and shedding ≤ 10 %. That would make
colocation the better choice: about 7 % cheaper, and with no KV network path to protect.

## 2. Why: the bottleneck at target concurrency

| Resource (5P2D at 30 req/s) | Utilisation `[MODELED]` |
|---|---|
| Prefill (0.091 s mean per request) | 30 × 0.091 / 5 = **0.55** |
| Decode (B = 491 at 33.5 ms; 14,675 tok/s/instance) | 30 × 285 / (2 × 14,675) = 0.29 |
| KV egress per prefill instance (RDMA / TCP pair) | 23.8 / 5 = 4.8 GB/s → 0.013 / 0.16 |
| **KV fan-in per decode instance** (RDMA / TCP pair) | 23.8 / 2 = 11.9 GB/s ≈ 95 Gb/s → 0.033 / **0.40** |

The service is **prefill-bound**. Over the same 115 s steady-state window the simulator measures a
prefill utilisation of 0.554, against 0.551 from the model. The network is sized on the receiving
side: with P > D every decode instance is a fan-in point. Over TCP, 5P1D would put
190 Gb/s (79 %) on one decode instance and become network-bound. With Chapter 15's TCP profile
(100 Gb/s achievable) even 5P2D needs 95 %, which is the chapter's "TCP infeasible" verdict.

## 3. When disaggregation helps and hurts `[SIMULATED]`

| Situation | Colocated | Disaggregated | Verdict |
|---|---|---|---|
| 30 req/s, 7 nodes, no chunking | TPOT p95 119 ms; ITL p99 257 ms (whole-prompt prefills stall the batch) | ITL p99 18 ms | Disaggregation fixes interference |
| 30 req/s, 7 nodes, fused 512-token chunks | TPOT 23.0 ms, ITL p99 31 ms; TTFT p95 6.0 s in the burst | 0.57 s with admission | Chunking also fixes the token cadence; colocation loses on burst TTFT *with this admission policy* |
| 30 req/s, 7 nodes, 1,024-token chunks + reference admission | TPOT 37.7 ms, ITL p99 58 ms; TTFT p95 2.5 s | — | Co-finalist; needs chunk-aware admission |
| ≈ 5.8 req/s on 2 nodes | Unchunked: TPOT 42 ms looks fine but ITL p99 is 157 ms. Chunked 1,024: TTFT 0.16 s, ITL p99 50 ms — passes | 1P1D: TTFT p95 1.50 s (one prefill instance blocked behind 32k prompts) | **Hurts at this small scale**; mean TPOT would have hidden the unchunked ITL failure |

I did not sweep load between those two points, so I do not claim a crossover rate. The next
experiment is a sweep from 5 to 30 req/s at equal GPU count.

## 4. RDMA versus TCP

Means hide the difference. I measure the second-token gap (exposed KV, plus the wait for a decode
slot, plus the first decode step) against the 100 ms ITL budget:

| Path (5P2D + admission) `[SIMULATED]` | Second-token gap p95 | Max |
|---|---|---|
| RDMA | 30 ms | 37 ms |
| TCP pair, not layer-pipelined | 81 ms | 393 ms |
| Chapter 15 single-port TCP, not pipelined | 162 ms | 894 ms |

The Chapter 15 TCP profile breaks the ITL budget for more than 5 % of requests. TPOT and ITL p99
barely move because each request has only one such gap, which is why it must be reported
separately. Layer pipelining hides most of the transfer inside prefill.

Even so, TCP still costs:
- two host copies and the CPU time for them;
- 40 % of each decode instance's share of an oversubscribed frontend (1.5:1 by bandwidth), which
  also carries storage and ingress.

RDMA prerequisites I will verify in the lab:
- `ib_write_bw --use_cuda` on each rail;
- ACS/IOMMU settings on the PCIe switches;
- locked-memory limits;
- RDMA path MTU 4096;
- `/GDRDMA` on NCCL channel lines (a loaded `nvidia_peermem` module alone is not proof).

## 5. QoS and isolation

The proposal puts KV in DSCP 26 / TC 3 together with training. A KV burst of up to 9.3 GB/s per
prefill node in that lossless class can trigger PFC pauses that propagate to W-TRAIN's collectives.
Because both use the same DSCP, KV cannot even be policed or measured separately.

**Corrected design: KV in a *lossy*, ECN-marked class.** KV uses DSCP 34 → TC 4 with no PFC; the
training PFC domain stays exactly as it is.
- **Scheduling:** DWRR with a bounded share (20 % `[ILLUSTRATIVE]`), so KV can never starve training.
- **ECN marking:** on TC 4 at a low queue threshold (for example, start marking around 150 KB and
  reach full probability around 1.5 MB `[ILLUSTRATIVE]`; tune per Chapter 9), with DCQCN on the
  KV queue pairs so senders slow down before buffers overflow.
- **Loss recovery:** the NIC's reliable-connection transport recovers by go-back-N. A mid-stream
  drop costs about one RTT (≈ 5 µs) plus resending the in-flight window (≈ 200–250 KB on ORION). A
  lost *tail* packet costs the QP's ACK timeout, 4.096 µs × 2^t. So the transfer engine sets a
  short local ACK timeout on KV QPs, e.g. t = 14 ≈ 67 ms, and loss stays rare because ECN acts first.

**Rejected alternative: a second lossless class.** PFC on priority 4 would need per-port headroom
of about 2 × the bandwidth-delay product (≈ 250 KB cross-rail) plus two maximum frames, ≈ 0.5 MB
per port per priority, on every port. It would also add a second set of pause-propagation risks.
I rejected it for a traffic type that tolerates rare retransmission.

**Encryption:** KV carries prompt content across a tenant boundary, so it is encrypted (or kept in
a separate trust domain).

## 6. Admission, speculative decoding, heterogeneity

**Admission.** A request is rejected when the queued backlog plus its own prefill time exceeds 90 %
of its TTFT SLO. At the 2.5× burst this sheds 7.1 % and keeps TTFT p95 at 0.57 s (9.49 s without).

**Speculative decoding.** The memory-bound textbook model (α = 0.8, c = 0.1, k = 4) promises
2.40×. At our operating batch of 491 that model fails. Verifying 5 tokens per sequence costs
2 × 70 × 10⁹ × 491 × 5 = 3.44 × 10¹⁴ FLOP.

| Decode MFU `[ILLUSTRATIVE]` | Verification step (vs 33.5 ms plain) | k = 1 | k = 2 | k = 4 |
|---|---|---|---|---|
| 0.6 (large-batch GEMM, assumed) | 76.4 ms | 1.64× | 1.51× | **1.25×** |
| 0.5 (same as prefill) | 90.9 ms | 1.43× | 1.30× | 1.08× |

I would enable it only with k = 1–2, or for low-batch, latency-sensitive traffic.

**Heterogeneous pools.** Hypothetical heterogeneous pools (4 compute-dense prefill + 1 HBM-rich
decode) reach $4.16 per million tokens in simulation. That is a sensitivity result, not a purchase
recommendation.

## 7. Failure scenarios (excerpt)

Losing one of the two decode instances drops all its in-flight sequences (their KV is lost) and
halves decode capacity. With 14,675 tok/s per instance and 8,550 tok/s needed, the surviving
instance still carries the load at 58 %, and its fan-in doubles to 79 % of a TCP pair (7 % of
RDMA). That is why I keep 5P2D rather than the cheaper 5P1D ($5.99 per million tokens) for 99.9 %
availability. A failed KV transfer is retried once to a different decode instance; if that also
fails, the request is re-prefilled.

---

**Instructor note.** Distinction because:
- the bottleneck is shown with every utilisation, on both network sides, and cross-checked against
  simulation over the same window;
- both "helps" and "hurts" are shown with numbers, and the chunked-prefill result is reported
  honestly;
- RDMA and TCP are compared by distribution and reconciled with Chapter 15;
- the QoS class is specified down to loss behaviour;
- speculative decoding is evaluated at the operating batch.

Points lost: no L2 calibration, and no load sweep.
