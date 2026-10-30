# Chapter 15 — LLM Inference and Serving Infrastructure

**Part IV — Distributed AI Systems · Course week 10**

An LLM request has two phases with opposite hardware appetites. Prefill is compute-bound. Decode
is bound by HBM bandwidth. Between them sits the KV cache, a per-request memory allocation that
usually sets how many users a GPU can serve. This chapter turns those mechanics into a capacity
model for W-INFER, the 70B chat model on the ORION reference cluster, and shows how to read a
serving trace when TTFT or TPOT SLOs break. It also follows the KV cache onto the network when
prefill and decode run in separate pools (disaggregated serving over RDMA or TCP), and it
evaluates speculative decoding. Batching, paged attention, preemption, quantization, Little's
law, goodput and tensor-parallel serving are covered with worked ORION numbers.

## Learning objectives

1. **Explain** why prefill is compute-bound and decode is memory-bandwidth-bound, and calculate
   each phase's arithmetic intensity for W-INFER on H100-class GPUs.
2. **Calculate** KV-cache bytes per token, the KV budget per replica, and the maximum concurrent
   sequences for a given model, precision, tensor-parallel (TP) degree and memory reservation.
3. **Model** decode throughput and TPOT from HBM bandwidth, and size a serving pool against TTFT
   and TPOT SLOs with Little's law and a simple queueing model.
4. **Diagnose** a serving trace with TTFT, TPOT/ITL, queue time, preemptions and replica
   telemetry, separating an arrival-driven queueing collapse from a KV-pressure preemption storm
   and from a slow replica.
5. **Compare** batching strategies, paged KV allocation, chunked prefill and quantization by
   their effect on memory, latency and quality.
6. **Design** a disaggregated prefill/decode deployment: KV bytes per request, aggregate network
   bandwidth, transport (RDMA vs TCP), QoS, isolation and failure behaviour.
7. **Evaluate** speculative decoding from acceptance rate, draft length and batch size.
8. **Recommend** one serving configuration for a latency-sensitive objective and another for a
   throughput-oriented one, with labelled evidence.

## Prerequisites

Chapter 4 (GPU execution, roofline), Chapter 5 (HX8 topology), Chapter 6 (measurement
discipline), Chapter 8 (RDMA), Chapter 9 (lossless QoS), Chapter 12 (all-reduce), Chapter 13
(GPUDirect RDMA). Python 3.10+ with numpy, pandas and pyyaml for the lab.

## Estimated time

| Activity | Time |
|---|---|
| Reading | 3.5–4 h |
| Exercises | 4–6 h |
| Lab (L1) | 4–5 h |
| L2/L3 extension (optional) | 4–8 h on hardware |

## Lab tier

**L1** (laptop; modeled and simulated). Optional **L2** (one GPU host with a serving engine) and
**L3** (two or more nodes with RDMA for disaggregated KV transfer) extensions are described in
[lab/README.md](lab/README.md) Section 9.

## Deliverable (course outline)

**Inference capacity model and tuning recommendation.** The definitive edition adds a KV-transfer
model, phase-specific SLOs and a serving architecture. See exercise DEL in
[exercises.md](exercises.md).

## File map

```text
ch15-llm-inference-serving/
├── README.md                     this chapter card
├── manuscript.md                 chapter text
├── exercises.md                  knowledge checks, worked problems, lab, troubleshooting,
│                                 design challenge, outline-mandated exercises, deliverable
├── lab/
│   ├── README.md                 lab guide (tasks, rubric, L2/L3 extensions)
│   ├── manifest.yaml             environment manifest
│   ├── check.py                  python check.py [--impl starter|solution]
│   ├── data/                     configs.yaml, requests.csv, token_gaps.csv, replica_telemetry.csv
│   ├── tools/generate_trace.py   seeded simulator that produces data/ (instructor copy only)
│   └── starter/serving_lab.py    learner module (functions raise NotImplementedError)
├── solutions/                    instructor only
│   ├── exercises-key.md
│   └── lab/serving_lab.py, INSTRUCTOR_NOTES.md
└── review/REVIEW.md              editorial review log
```

## Connections

This chapter builds on Chapters 4, 5, 8, 9, 12 and 13. Chapter 17 (scheduling serving pods),
Chapter 18 (SLOs and alerts), Chapter 19 (tenant isolation) and Chapter 21 (cost per token) build
on it. **Capstone D** (production LLM inference platform) and **Capstone H** (disaggregated
serving) apply it directly.
