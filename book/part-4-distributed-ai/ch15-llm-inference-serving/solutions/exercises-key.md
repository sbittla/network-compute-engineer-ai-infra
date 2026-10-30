# Chapter 15 — Exercise Answer Key (instructor only)

Conventions: values are `[MODELED]` unless stated otherwise. GPU constants are H100-class
`[VENDOR-SPEC, 2026-10]`: HBM 3.35 TB/s and 80 GB per GPU, 989 TFLOP/s dense BF16, 1,979 TFLOP/s
dense FP8. Planning factors are `[ILLUSTRATIVE]`: HBM efficiency 0.70, 3 ms step overhead,
prefill MFU 0.40, memory fraction 0.90, 2 GB reserve per GPU, 16-token blocks. Each number was
computed by hand and then re-checked with `solutions/lab/serving_lab.py`.

Useful constants:

* KV/token (BF16) = 327,680 B; FP8 = 163,840 B.
* Bytes per 16-token block: BF16 5,242,880 B; FP8 2,621,440 B.
* Prefill seconds per token: TP = 4 FP8 (or TP = 8 BF16) = 1.4e11 ÷ 3.166e15 = 44.2 µs;
  TP = 2 FP8 = 88.4 µs.
* Decode-step model for TP = 4 FP8: t_d = 10.463 ms + (ctx × 327,680 ÷ 9.38e12) × B.

---

## A. Knowledge checks

**K1.** Decode at B = 32 does about 2N × 32 FLOP while streaming about 2N bytes of BF16 weights,
for an intensity of about 32 FLOP/B. Attention over the KV cache runs at about 8 FLOP/B with GQA.
Both are far below the BF16 ridge of 989/3.35 ≈ 295 FLOP/B, so decode is bandwidth-bound. A
2,048-token prefill reuses each weight 2,048 times, for an intensity of about 2,048 FLOP/B, well
above the ridge, so it is compute-bound.
*Marking:* 2 pts each intensity, 1 pt ridge. *Common mistake:* computing intensity per token
instead of per weight read.

**K2.** TTFT = first_token − arrival. TPOT = (finish − first_token)/(n_out − 1). ITL = each
t_{i+1} − t_i. Example: a 2k-token prefill admitted into a running batch stalls every sequence
for about 90 ms once. Over 255 gaps that adds only about 0.35 ms to mean TPOT, but it appears as a
90 ms+ ITL outlier. Preemption-recompute stalls and the KV transfer delay before token 2 in
disaggregated serving behave the same way.
*Common mistake:* defining TPOT as e2e/n_out, which includes TTFT.

**K3.** (Marking 4: mechanism 2, failure mode 1, recompute vs swap cost 1.) Contiguous per-request reservation at maximum length wastes memory through
over-reservation and fragmentation. The vLLM paper reports that only about 20–40 % of KV memory
held token state in prior systems. Paging allocates 16-token blocks on demand, so at most one
partial block per sequence is wasted. The new failure mode is that the pool can run out while
sequences are decoding. The scheduler must then preempt by recompute (re-prefilling prompt plus
generated tokens) or by swap (copying blocks to host memory over PCIe). Either one stalls the
replica, and repeated preemption is a storm.

**K4.** (Marking 4: one point per strategy, 1 for the interference mechanism.) Static batching runs a fixed batch to completion, so early finishers idle their slots.
Dynamic batching forms a batch on size or timeout but still runs it to completion. Continuous
batching admits and retires sequences at every iteration (Orca). Interference arises because a
newly admitted request's prefill has to occupy an iteration, or part of one with chunking. During
that iteration the running sequences get no token or a slower one.

**K5.** (Marking 4: two definitions 2, scenario 2. *Common mistake:* calling throughput of
completed requests "goodput".) DistServe defines goodput as the maximum request rate at which a target fraction (for
example 90 %) of requests meet both TTFT and TPOT SLOs. Operationally, on one trace, it is
SLO-meeting requests per second. Throughput can rise while goodput falls. Example: raising the
concurrency cap from 48 to 256 serves more tokens per second, but every request's TPOT rises past
50 ms, so goodput drops toward zero. In the lab trace, throughput is 7.57 req/s and goodput is
3.69 req/s `[SIMULATED]`.

**K6.** (Marking 3: both byte counts 2, concurrency effect 1.) With GQA: 2 × 80 × 8 × 128 × 2 = 327,680 B. Without (64 KV heads): 2 × 80 × 64 × 128 × 2 =
2,621,440 B. That is 8× more, so for a fixed KV budget, maximum concurrency (or total context) is
8× lower. For example, 156 sequences of 4k tokens would become 19 per TP = 4 FP8 replica.

**K7.** (Marking 4: what the counter measures 2, two better signals 2.) `utilization.gpu` is the fraction of the sample period during which at least one kernel
was executing. It says nothing about how many SMs were active, tensor-core use or HBM bandwidth.
A memory-bound decode loop reads 100 % at a small fraction of peak. Better signals: (1) DCGM
DRAM-active (field 1005) for bandwidth saturation, plus tensor or SM active for compute; (2)
engine-level signals such as running vs the concurrency cap, KV usage, waiting-queue depth and
step time vs batch. These map directly to the binding resource.

**K8.** (Marking 4: each estimate with stated assumptions 2.) Recompute costs 10,000 × 88.4 µs ≈ 0.88 s of prefill on TP = 2 FP8 at 40 % MFU, and it
stalls every co-scheduled sequence. Swap moves 10,000 × 327,680 = 3.28 GB. With TP = 2 each GPU
holds half (1.64 GB) on its own PCIe Gen5 x16 link at about 50 GB/s, so about 33 ms out and 33 ms
back, plus host memory pressure. Swap is cheaper per event for long contexts but adds PCIe and
host-memory contention. Recompute needs no host memory. *Accept* any stated, reasonable
bandwidth assumption.

---

## B. Worked problems

**W1.**
(a) Budget = 8 × 80e9 × 0.90 − 70e9 − 8 × 2e9 = 576e9 − 70e9 − 16e9 = **490 GB**. FP8 KV blocks =
⌊490e9 ÷ 2,621,440⌋ = **186,920**. An 8,192-token sequence needs 8,192/16 = 512 blocks, so the
maximum is ⌊186,920 ÷ 512⌋ = **365 sequences**.
(b) BF16 KV: ⌊490e9 ÷ 5,242,880⌋ = 93,460 blocks, so ⌊93,460 ÷ 512⌋ = **182 sequences**. FP8 KV
doubles concurrency.
(c) Bytes per step = 70e9 + 64 × 6,000 × 163,840 = 70e9 + 62.915e9 = 132.915e9 B.
Lower bound = 132.915e9 ÷ (8 × 3.35e12) = 132.915e9 ÷ 26.8e12 = **4.96 ms**, giving 64 ÷ 0.00496 =
**12,905 tokens/s**.
Planning value = 3 ms + 132.915e9 ÷ 18.76e12 = 3 + 7.085 = **10.08 ms**, giving **6,346
tokens/s**.
*Marking:* 3 + 2 + 5 pts. *Common mistakes:* forgetting the reserve; using BF16 KV bytes in (c);
using GiB for capacity without saying so.

**W2.**
(a) t_p = 2 × 70e9 × 4,096 ÷ 3.166e15 = **181.1 ms**. The quadratic attention term would add
about 6.9 ms (2 × 80 × 4,096² × 8,192 ÷ 3.166e15); the lab model omits it, and students who include
it should be credited. Prefill demand = 25 × 0.1811 = **4.53 replica-s/s**.
(b) Average decode context = 4,096 + 256 = 4,352 tokens, so the per-sequence step coefficient is
4,352 × 327,680 ÷ 9.38e12 = 0.15203 ms.

| Replicas | λ_r | ρ_prefill | Mean TTFT | Mean TPOT | B |
|---|---|---|---|---|---|
| 6 | 4.17 | 0.755 | 0.460 s | **unstable** | — |
| 8 | 3.13 | 0.566 | 0.299 s | 54.8 ms | 87.7 |
| 10 | 2.5 | 0.453 | 0.256 s | 29.7 ms | 38.0 |
| 12 | 2.08 | 0.377 | 0.236 s | 22.7 ms | 24.2 |

Fixed point for 10 replicas: B = 2.5 × 512 × TPOT = 1,280 × TPOT. Then
TPOT × (1 − 0.4528) = 0.010463 + 0.00015203 × 1,280 × TPOT = 0.010463 + 0.19460 × TPOT, so
TPOT = 0.010463 ÷ (0.5472 − 0.1946) = 0.010463 ÷ 0.3526 = **29.7 ms**.
Six replicas are unstable because the decode demand term c·λ_r·O = 0.00015203 × 4.17 × 512 =
0.324 exceeds the available fraction 1 − ρ = 0.245. Decode cannot keep up, and the number of
sequences grows without bound.
(c) Choose **10 replicas** (mean TPOT 29.7 ms ≤ 35 ms), plus 2 for N+1 and bursts, for 12
replicas on 6 HX8 nodes. Worst unchunked ITL = t_d(38) + t_p = (10.46 + 0.152 × 38) + 181.1 ≈
16.2 + 181.1 = **197 ms**. Recommend chunked prefill.
(d) Full length is 4,608 tokens = 288 blocks, so ⌊40,054 ÷ 288⌋ = **139 sequences** per replica,
well above B = 38.
*Marking:* (a) 2, (b) 5, (c) 2, (d) 1. *Common mistakes:* applying the TTFT SLO to the mean;
ignoring instability; omitting the (1 − ρ) stall factor.

---

## C. Hands-on lab

See `solutions/lab/INSTRUCTOR_NOTES.md` for every expected value and the planted anomalies.
Grade with the rubric in `lab/README.md` Section 8. For the report, require that:

* the configuration recommendation cites the TPOT figures (11.7 vs 20.2 ms) and tokens/s/node
  (2,740 vs 12,678);
* each anomaly has symptom → discriminating evidence → cause → mitigation:
  * **Burst:** arrivals 4.3× median, running = 48 cap on every replica, KV 30–43 %, so it is
    slot-bound. Mitigate with gateway admission control or load shedding, or more replicas.
  * **Storm:** arrivals flat, KV 98–100 %, preemption counter rising, running below the cap with a
    queue. Mitigate with per-tenant limits, KV-aware routing, or by moving long contexts to a
    larger-KV pool.
  * **Slow replica:** r3 median TPOT 75.5 ms vs peers 42.5 ms, the same busy %. Mitigate by
    draining it and checking clocks and power limits.
* the Part C memo states that at 6P+2D the TCP design needs 107 % of achievable link bandwidth
  (infeasible) while RDMA runs at 7.9 %, and labels every value MODELED.

---

## D. Troubleshooting case — T1 model answer

**Ranked hypotheses.**

1. **The fine-tuning job shares the decode nodes' NICs or rail ports in the lossless class.**
   *For:* onset aligned to the 14:00–15:30 job. RX per decode node (sum of its four KV rails)
   rose from 108 to 330 Gb/s. KV demand is about 107 Gb/s per decode replica (about 27 Gb/s per
   rail), so about 220 Gb/s of extra traffic is arriving at those nodes. ECN marks rose about 800× and PFC pauses appeared. *Against:* not yet proven
   that the job runs there.
2. **Fabric hot spot elsewhere (spine or leaf uplinks) from the job, with congestion spreading
   through PFC.** *For:* PFC can propagate congestion beyond the hot link. *Against:* RX
   throughput on the decode ports themselves rose, which points to local traffic.
3. **Higher KV demand.** *Against:* the request rate moved only from 39 to 41 req/s (+5 %), which
   cannot explain a 37× rise in transfer p99. Rejected.
4. **A degraded NIC, optic or link on the decode side.** *Against:* the effect is periodic and
   time-of-day aligned. Physical faults do not follow a calendar. Check symbol and FEC errors
   anyway (Chapter 10).

**Discriminating tests.**

* `squeue -j <jobid> -o %N` or `scontrol show job <jobid>` for the fine-tune job, to get its
  node list. Intersect it with the decode nodes `orion-n27` and `orion-n28` (inference partition, rack-07) (for example, the job
  may have been placed on their idle GPUs 4–7). If they overlap, hypothesis 1 is confirmed.
* On a decode node during the window, read per-priority NIC counters, for example
  `ethtool -S <iface> | grep -E 'prio3_(bytes|pause)'` on mlx5-class NICs (counter names are
  driver-specific; verify). This shows whether TC 3 bytes and pauses rise on the KV rails.
* Leaf telemetry: per-port ECN and PFC counters across all rail leaves. If only decode-facing
  ports are hot, the cause is local (hypothesis 1). If spine uplinks are hot fabric-wide, it is
  hypothesis 2.
* NCCL debug output of the job (`NCCL_DEBUG=INFO` in the *job's* environment, a job-owner change)
  shows which NICs its ranks use.

**Still needed:** the job's node list, its NCCL NIC selection, and port counters on non-decode
ports for comparison.

**Mitigation (safe, reversible).** Ask Platform to exclude the decode nodes from the fine-tune
job's eligible nodes for the next run, by job-level exclusion or a Slurm reservation for the
inference nodes. Do not drain nodes running other jobs without the owners' agreement, and do not
modify switch QoS during the incident.

**Structural fix (through change control, Chapter 20).** Use separate node pools or partitions
for inference and training. If links must be shared, give KV its own traffic class with ECN and
a guaranteed bandwidth share (Chapter 9), and admit inference-pool nodes only to the inference
scheduler.

**Validation.** Over the next five 14:00–15:30 windows, KV transfer p99 must be under 10 ms,
token-2 ITL p99 under 30 ms (baseline ≈ 24 ms; modeled mean worst case 21.1 ms), ECN marks on decode ports under 100/s, and PFC pauses on those
ports must be zero. Compare against the 13:00–14:00 baseline with the same metrics.

*Marking (20):* hypotheses with for/against 6, tests with real sources 6, mitigation safety 4,
validation numbers 4. *Common mistakes:* blaming KV volume without checking the request rate;
proposing a fabric-wide QoS change during the incident; treating correlation with the calendar as
proof without the node-list check.

---

## E. Design challenge — D1 model answer

**Prefill** (8,192 tokens on TP = 4 FP8): linear term 2 × 70e9 × 8,192 ÷ 3.166e15 = 362.2 ms;
attention term 2 × 80 × 8,192² × 8,192 ÷ 3.166e15 = 27.8 ms; total **t_p = 390.0 ms**. Demand =
20 × 0.390 = **7.80 replica-s/s**.

**Prefill pool:**

| P | ρ | Mean TTFT | Approx. p95 TTFT (t_p + 3 × W_q) |
|---|---|---|---|
| 11 | 0.709 | 0.865 s | ≈ 1.82 s ✗ |
| 12 | 0.650 | 0.752 s | ≈ 1.48 s (borderline) |
| 13 | 0.600 | 0.682 s | ≈ 1.27 s ✓ |

**Decode pool** (average context 8,192 + 150 = 8,342 tokens): at end of generation each
sequence holds 8,492 tokens = 531 blocks, so 75 sequences fit per replica in BF16 KV, or 150 in
FP8 KV.

| D | TPOT (mean) | B per replica |
|---|---|---|
| 3 | 25.1 ms | 50.2 |
| 4 | 18.6 ms | 27.9 |
| 5 | 16.1 ms | 19.3 |

Choose **13P + 4D = 17 replicas**: 8.5 nodes, rounded up to 9 HX8, plus 1 spare, for 10 nodes.

**Network:** KV per request = 8,192 × 327,680 = 2.684 GB. Aggregate = 20 × 2.684e9 × 8 =
**429.5 Gb/s**, and 107.4 Gb/s per decode replica. Over RDMA that is 7.9 % of 1,360 Gb/s
achievable, with a transfer time of 15.8 ms per request (hidden by per-layer streaming: about
0.2 ms per layer against 4.9 ms of prefill per layer). Over TCP it is 107 % of the 100 Gb/s
achievable, so **TCP is infeasible**. Choose RDMA on the decode replicas' rail-local NICs, in a
dedicated traffic class or on dedicated inference rails. FP8 KV would halve the demand to 215
Gb/s.

**Shared alternative (acceptable if argued):** 16 replicas give ρ = 0.487, mean TTFT 0.575 s and
mean TPOT 26.0 ms, but a worst unchunked ITL of 403 ms. With 512-token chunks, about half of the
decode steps carry a 22.6 ms chunk, so ITL is bimodal at about 13 and 36 ms and TPOT p95 lands
near the 40 ms SLO. Disaggregation buys headroom on TPOT.

**Failure table:** losing a decode replica drops the KV of about 28 sequences. They are
re-prefilled at about 0.4 s each on the prefill pool (an extra 11 replica-seconds of load),
gated by admission control. Losing a prefill replica raises ρ on the other 12 to 0.65, which is
still within SLO. A KV transfer timeout is retried once, then the request falls back to local
prefill.

**L2/L3 measurements:** HBM efficiency and step overhead at B ≈ 28 with an 8k context; actual
prefill MFU at 8k (including the attention kernel); RDMA throughput between the rail-local NICs
(`ib_write_bw`) and KV bytes per request from the connector.

*Marking (25):* sizing 8, network budget 5, transport decision with numbers 4, failure table 4,
measurement plan 2, labelling 2. Accept a different P:D split or the shared design if the numbers
support it.

---

## F. Outline-mandated exercises

**O1.** Usable HBM is 4 × 80 × 0.90 = 288 GB. After 70 GB of weights and 8 GB of reserve, the KV
budget is 210 GB.

| Seq length | B = 16 | B = 64 | B = 128 | Max seqs (KV 210 GB) |
|---|---|---|---|---|
| 1,024 | 70 + 5.4 = 75.4 GB | 70 + 21.5 = 91.5 GB | 70 + 42.9 = 112.9 GB | 625 |
| 4,096 | 70 + 21.5 = 91.5 GB | 70 + 85.9 = 155.9 GB | 70 + 171.8 = 241.8 GB | 156 |
| 16,384 | 70 + 85.9 = 155.9 GB | **70 + 343.6 = 413.6 GB ✗** | **70 + 687.2 = 757.2 GB ✗** | 39 |

KV memory grows as B × context, so at long context the KV term dwarfs the weights. Concurrency
then falls inversely with sequence length, and memory, not compute, binds.

**O2.** From Lab Part B `[SIMULATED]`:

| Segment | req/s | out tok/s | TTFT p50 / p95 | ITL p50 / p99 (sampled) | Queue p95 | GPU busy | KV max | Waiting (mean) |
|---|---|---|---|---|---|---|---|---|
| Baseline 0–230 s | 6.00 | 1,216 | 0.138 / 0.449 s | 21.8 / 216 ms | 0.11 s | 97.6 % | 13.5 % | 0.1 |
| Burst episode 240–345 s | 14.8 | 2,980 | 11.8 / 28.8 s | 26.9 / 444 ms | 28.5 s | 100 % | 43.3 % | 46.1 |
| Storm episode 465–600 s | 5.81 | 1,434 | 0.278 / 33.2 s | 37.2 / 386 ms | 32.6 s | 100 % | 100 % | 6.0 |

GPU busy is about 98–100 % in all three segments, so it cannot distinguish healthy from
overloaded or slot-bound from memory-bound. The baseline ITL p99 of 216 ms reflects unchunked
prefill stalls, which is expected for this pool.

**O3.** Latency objective: **L-tp8-bf16**, with TPOT 11.7 ms (about 86 tok/s per user) against
20.2 ms. Throughput objective: **T-tp4-fp8**, with 12,678 against 2,740 tok/s per node (4.6×).
Flip conditions:
(i) If the TPOT SLO tightens below about 20 ms (for example 15 ms), T fails the SLO and the
throughput recommendation becomes L.
(ii) If contexts grow so that T's 156 sequences at 4k (39 at 16k) cap the batch below 128, T's
throughput advantage shrinks.
(iii) If FP8 quality is unacceptable for the product, T is excluded regardless of the numbers.

**O4.** KV per request = 8,192 × 327,680 = **2,684,354,560 B (2.68 GB)**. Aggregate =
10 × 2.684e9 × 8 = **214.7 Gb/s**, the same as 40 req/s at 2k, because prompt tokens per second
are equal. Per decode replica (2) = 107.4 Gb/s. Transfer time: RDMA 30 µs + 2.684e9 ÷ 170e9 =
**15.8 ms**; TCP 1 ms + 2.684e9 ÷ 12.5e9 = **215.7 ms**.

| Design | ρ_prefill | Mean TTFT | Mean TPOT | Worst ITL | Link util |
|---|---|---|---|---|---|
| Shared (8) | 0.453 | 0.512 s | 23.0 ms | 375 ms | — |
| Disagg RDMA (6P+2D) | 0.604 | 0.638 s | 16.7 ms | 32.5 ms | 7.9 % |
| Disagg TCP (6P+2D) | 0.604 | 0.638 s | 17.5 ms | 232 ms | 107 % (infeasible) |

These are lab-model values (linear prefill, 362.2 ms). The disaggregated mean TTFT (0.64 s)
leaves little margin for a 0.8 s p95 target, so the prefill pool needs a 7th replica at this
prompt length.

*Per-layer overlap:* prefill per layer = 362.2 ÷ 80 = 4.53 ms. KV per layer = 2.684e9 ÷ 80 =
33.6 MB, which takes 0.20 ms over RDMA and 2.68 ms over TCP. Both are below 4.53 ms, so an
*uncontended* TCP link can in principle hide the transfer behind prefill if the engine streams
per layer. At 107 % utilization, though, the link cannot carry the aggregate at all, and the CPU
cost remains. With FP8 KV the TCP load drops to 54 %.

*FP8 KV:* 107.4 Gb/s aggregate (53.7 Gb/s per decode replica), 7.9 ms per request over RDMA,
108 ms over TCP.

*Labelling:* all values are MODELED. Efficiency, fixed latency, per-layer streaming and
transfer-tail behaviour need L3 measurement.

**O5.** Expected tokens per step E = (1 − α^(k+1))/(1 − α):

| α \ k | 2 | 4 | 8 |
|---|---|---|---|
| 0.6 | 1.96 | 2.31 | 2.48 |
| 0.8 | 2.44 | 3.36 | 4.33 |
| 0.9 | 2.71 | 4.10 | 6.13 |

Speedup with verify cost 1 (memory-bound), E ÷ (0.05k + 1):

| α \ k | 2 | 4 | 8 |
|---|---|---|---|
| 0.6 | 1.78 | 1.92 | 1.77 |
| 0.8 | 2.22 | 2.80 | 3.09 |
| 0.9 | 2.46 | 3.41 | 4.38 |

Verification cost at B = 128 on T-tp4-fp8, derived from the roofline. Verification streams the
same bytes as a decode step (17.19 ms of HBM time at 70 % efficiency), and its compute is
B(k + 1) tokens × 2 × 70e9 FLOP ÷ (4 × 1,979e12 × 0.40) = B(k + 1) × 44.2 µs. Then
v_k = (max(compute, 17.19 ms) + 3 ms) ÷ 20.19 ms:

* k = 2: 384 tokens → 16.98 ms compute, still below 17.19 ms (memory-bound), so v = 1.00.
* k = 4: 640 tokens → 28.30 ms (intensity 2 × 640 = 1,280 FLOP/B > 591), so v = 31.30 ÷ 20.19 = 1.55.
* k = 8: 1,152 tokens → 50.93 ms, so v = 53.93 ÷ 20.19 = 2.67.

Speedup at B = 128, E ÷ (0.05k + v_k):

| α \ k | 2 (v = 1.00) | 4 (v = 1.55) | 8 (v = 2.67) |
|---|---|---|---|
| 0.6 | 1.78 | 1.32 | 0.81 |
| 0.8 | 2.22 | 1.92 | 1.41 |
| 0.9 | 2.46 | 2.34 | 1.99 |

Recommendation: on the interactive (small-batch) tier, use k = 4, and k = 8 only if α ≥ 0.9 is
measured, because gains beyond k = 4 are small at α = 0.6–0.8 and longer drafts cost compute and
memory. On the throughput tier, **use a short draft (k = 2)**: verification stays memory-bound
and keeps about 1.8–2.5×. k = 8 is a net loss at α = 0.6. Re-derive v_k for your real batch size.
*Marking:* E table 3, memory-bound table 3, the derivation of v_k 3, recommendation 1.
*Common mistake:* guessing a constant verification cost instead of deriving it per k.

---

## G. Reflection — guidance

Marking for each R item: 3 points. Award 1 for the core claim, 1 for the supporting numbers or
evidence, and 1 for naming the instrument or measurement that would settle it.

* **R1.** HBM efficiency and step overhead (they set TPOT), prefill MFU (it sets TTFT and the pool
  size), and the KV-transfer efficiency and tail (they set the disaggregation decision). Each
  scales a headline number linearly or worse.
* **R2.** The sample covers 227 requests and about 72k gaps. Gaps within one request are
  correlated (a single stall hits many co-scheduled requests), so the effective sample size is
  much smaller than 72k. p99 is usable for trends. p99.9 (about 72 points) is dominated by a few
  stall events and must not be used for SLO compliance. Increase sampling or log per-request max
  ITL instead.
* **R3.** Growth in prompt tokens per request (for example RAG adoption) or in the prompt:output
  ratio. The first signal is ρ_prefill (the prefill share of iterations) rising and ITL p99
  rising with it, before TTFT breaches.
* **R4.** A quality evaluation at the tenant's real context lengths (8–12k), comparing BF16 and
  FP8 KV on task metrics; a canary with per-tenant quality signals; and confirmation that the
  engine's KV scaling method is supported for the model. A memory saving is not evidence of
  safety.

---

## H. Deliverable — marking guidance

A strong memo:

* recommends the shared pool of 8 × TP = 4 FP8 replicas with chunked prefill and 5 nodes including
  N+1, or argues an alternative with numbers;
* sets latency tier L and throughput tier T;
* gives the KV network budget (about 215 Gb/s at 40 req/s with 2k prompts, linear in prompt tokens
  per second) and the RDMA transport choice;
* defines the TTFT, TPOT, ITL p99, preemption and per-replica TPOT alerts from the runbook;
* lists the L2/L3 measurements with the manifest fields from `lab/manifest.yaml`.

Deduct heavily for any modeled number presented as measured.
