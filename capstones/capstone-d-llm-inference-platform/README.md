# Capstone D: Production LLM Inference Platform

You will design the platform that serves W-INFER, Halcyon AI's 70B chat model, on ORION HX8 nodes.
That means the service architecture, a capacity model, SLO/SLI definitions, a load-test plan,
TTFT/inter-token-latency/throughput results (modeled and simulated at L1, measured if you take the
extension), a rollout and rollback plan, and a cost analysis. The starter kit gives you a request-level
discrete-event simulator of continuous batching, which you complete and then use to compare serving
configurations under the same trace. The capstone is about the decisions an inference platform
engineer must defend: how much KV cache a replica really has, why the configuration with the best
throughput number can be the wrong choice, why mean TPOT can hide token stalls that ITL tails reveal,
and why rejecting requests is not a way to meet a latency SLO.

## Audience and prerequisites

**Audience (course outline, Section 16):** AI Platform Engineer, Inference Infrastructure Engineer.

**Recommended preparation:** Chapters [15](../../book/part-4-distributed-ai/ch15-llm-inference-serving/),
[6](../../book/part-2-accelerated-compute/ch06-gpu-performance-engineering/),
[17](../../book/part-5-production-operations/ch17-kubernetes-slurm-scheduling/),
[18](../../book/part-5-production-operations/ch18-observability-slos-incident-response/),
[20](../../book/part-5-production-operations/ch20-automation-safe-change/) and
[21](../../book/part-5-production-operations/ch21-capacity-power-economics/).
This capstone covers single-pool (colocated prefill and decode) serving.
[Capstone H](../capstone-h-disaggregated-llm-serving/) is the follow-on for disaggregated prefill/decode pools.

## Scenario

Inference serves W-INFER ([REFERENCE_CLUSTER.md](../../docs/REFERENCE_CLUSTER.md) §3) from ORION's
Kubernetes partition. The model has 70B parameters (BF16 ≈ 140 GB, FP8 ≈ 70 GB), with KV cache of
320 KiB per token in BF16. The SLOs are TTFT p95 ≤ 800 ms for prompts up to 2k tokens (end to end; 30 ms
is budgeted for the frontend), TPOT p95 ≤ 50 ms, ITL p99 ≤ 100 ms `[ILLUSTRATIVE]` and 99.9 % availability. Most traffic is chat. A new enterprise tenant sends retrieval-augmented
requests with ≈ 32k-token prompts, about 2 % of requests but a large share of the prompt tokens. Four
configurations are on the table: two BF16 TP = 8 variants (chunked prefill versus large unchunked
batches), FP8 TP = 4 with two replicas per node, and a BF16 variant that caps context at 8k. A vendor
sizing sheet has also been circulating. Finance wants a cost per million tokens; SRE wants rollback
gates before anything ships.

## Problem statement

Choose and justify a serving configuration and fleet size for the traffic forecast that meets the SLOs
with stated headroom. Define how the SLOs are measured and enforced, how changes are rolled out and
rolled back, and what each million tokens costs. Success means:

1. a capacity model with every byte accounted for (weights, reserve, KV budget) and the iteration
   roofline that explains TTFT and TPOT;
2. simulated SLIs per configuration and load level over ≥ 5 independent traces (median and range,
   unstable points flagged rather than given a p95), with the highest SLO-compliant load identified;
3. a recommendation that treats rejected requests as failures and handles the long-context tenant
   explicitly;
4. rollout gates that would have caught each trap in the candidate set;
5. a cost per million tokens (total tokens as the headline, since the mix is input-dominated) quoted at an
   SLO-compliant operating point.

## Required artifacts

The first seven rows are the Capstone D artifacts from the course outline (Section 16). The remaining
rows are required of every capstone.

| Artifact | Template | Expected evidence label |
|---|---|---|
| Service architecture | [design-doc.md](templates/design-doc.md) §2, [adr-serving-config.md](templates/adr-serving-config.md) | design |
| Capacity model | [capacity-model.md](templates/capacity-model.md), [capacity-model.csv](templates/capacity-model.csv) | `[MODELED]`, `[SIMULATED]` |
| SLO/SLI definitions | [slo-sli-spec.md](templates/slo-sli-spec.md) | — |
| Load-test plan | [load-test-plan.md](templates/load-test-plan.md) | — |
| TTFT/inter-token latency/throughput results or modeled estimates | [results-table.csv](templates/results-table.csv) | `[SIMULATED]`; `[MEASURED]` if L2 |
| Rollout and rollback plan | [rollout-rollback-plan.md](templates/rollout-rollback-plan.md) | — |
| Cost analysis | [cost-analysis.md](templates/cost-analysis.md) | `[MODELED]` |
| Problem statement; architecture; assumptions | [design-doc.md](templates/design-doc.md) §1–3, [assumptions-register.csv](templates/assumptions-register.csv) | |
| Implementation or simulation boundary | [design-doc.md](templates/design-doc.md) §4 | |
| Test plan; results | [load-test-plan.md](templates/load-test-plan.md), [results-table.csv](templates/results-table.csv) | kept apart by label |
| Failure analysis; security considerations | [design-doc.md](templates/design-doc.md) §10–11 | |
| Final engineering review | [final-engineering-review.md](templates/final-engineering-review.md) | |

## Milestones

| Milestone | Week | What you hand in |
|---|---|---|
| M0: choose | 8 | Capstone choice; read the inputs, including the vendor sheet |
| M1: proposal | 10 | Problem statement, architecture sketch, capacity model (checks 01–03) |
| M2: simulator | 12 | Checks 01–08; results for all configurations at 1.0× and 2.0× |
| M3: draft | 13 | Load sweep, SLO spec, rollout plan, cost analysis; peer review booked |
| M4: final | 14 | Complete pack, final engineering review, 15-minute presentation |

## Tier options

| Tier | Scope | What it adds |
|---|---|---|
| **L1 (required)** | [starter-kit](starter-kit/) capacity model and simulator | Full marks achievable with correct labels |
| **L2 (optional)** | Run a supported open model and serving stack; replay the trace shape; compare two configurations | `[MEASURED]` TTFT/ITL/throughput, and a calibration of the simulator |
| **L3 (optional)** | Multi-replica routing with a canary and a rollback drill | `[MEASURED]` rollout behaviour |

**Advanced extension (course outline):** run a supported open model and serving stack, and compare
configurations under identical workload and hardware conditions. See the
[starter-kit README, Section 8](starter-kit/README.md#8-extensions-l2l3).

> **Realism boundary:** The simulator is a planning tool. Its iteration cost is a roofline with
> illustrative efficiencies, and it ignores kernel shape effects, tensor-parallel communication
> variance, scheduler CPU time, tokenization, networking and prefix caching. Expect real knees to sit
> elsewhere. The ranking and the mechanisms (head-of-line blocking, memory-bound decode, the cost of
> idle capacity) are what transfer.

## How the chapters map to the artifacts

| Artifact | Chapters |
|---|---|
| Architecture, request path | 15, 17 |
| Capacity model (KV, roofline) | 4, 6, 15 |
| SLOs, error budgets, burn-rate alerts | 18 |
| Load-test plan | 15, 22 |
| Rollout/rollback | 20 |
| Cost | 21 |
| Security, multi-tenancy | 19 |

## Grading

Graded with the [capstone rubric](../RUBRIC.md). For Capstone D, excellent work looks like this:

| Dimension | What excellent looks like in Capstone D |
|---|---|
| Problem framing and assumptions (10) | Traffic forecast, tenant mix and FP8 quality status are explicit assumptions with validation plans |
| Architecture and technical correctness (20) | KV arithmetic in KiB/GB without unit slips; the roofline explains why prefill is compute-bound and decode memory-bound; the request path is drawn end to end |
| Implementation / reproducibility (15) | All 11 checks pass; one command reproduces every sweep |
| Measurement and analysis (20) | Load sweeps find each configuration's knee; comparisons at matched load; goodput and error rate are reported next to throughput; simulated and measured never merged |
| Reliability, security and operations (15) | Canary gates with burn-rate logic; failure analysis covers TP-group loss and KV exhaustion; tenant isolation |
| Troubleshooting and engineering judgment (10) | Spots the c2 and c4 traps and the long-context head-of-line blocking, and changes the architecture (routing) rather than only the knobs |
| Communication and portfolio quality (10) | A reviewer sees the recommendation, its evidence and its cost on one page |

## File map

```text
capstone-d-llm-inference-platform/
├── README.md            this brief
├── templates/           design doc, ADR, capacity model (md + csv), SLO/SLI spec, load-test plan, results,
│                        rollout/rollback, cost analysis, assumptions, final review
├── starter-kit/         L1 capacity model + simulator: data/, tools/ (instructor edition only), starter/serving.py, check.py, README.md
├── instructor/          grading guide, exemplar, reference implementation (removed in student edition)
└── review/REVIEW.md     editorial review log
```
