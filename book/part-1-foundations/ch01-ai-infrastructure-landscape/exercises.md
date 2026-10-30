# Chapter 1 — Exercises

Difficulty: ★ foundational · ★★ intermediate · ★★★ advanced. Tier: L1 laptop/paper · L2 single GPU
host · L3 multi-node GPU + RDMA. Use ORION values from `docs/REFERENCE_CLUSTER.md` unless an exercise
changes them, and label every number you produce (`[MODELED]`, `[ILLUSTRATIVE]`, `[MEASURED]`, …).

**Chapter deliverable (course week 1):** annotated architecture diagrams (training and online
inference) and a one-page workload comparison. Exercises 1.1, 1.2, and the lab together produce it.

---

## Outline-mandated exercises

### Exercise 1.1 — Reference architectures for training and inference ★★ · L1

Draw two reference architectures on ORION: (a) the W-TRAIN model-training workload and (b) the
W-INFER online-inference service. For each, show compute, scale-up network, scale-out network,
frontend network, storage, orchestration, and observability components, and the data paths between
them. Annotate each diagram with: the dominant data flow and its approximate volume (per step or per
request); for every layer, one dependency the workload has on it and the first signal you would see
if it degraded; and the failure domain of the workload (what fails together).

**Evidence required:** two diagrams (Mermaid, draw.io, or hand-drawn and photographed) each with ≥ 6
labelled components and ≥ 4 labelled data paths with volumes; a dependency table per workload (layer,
component, dependency, first signal); one paragraph contrasting their failure domains.

### Exercise 1.2 — Scale-up versus scale-out for two workloads ★★ · L1

Two hypothetical workloads run on ORION. Profiles are per GPU per step `[ILLUSTRATIVE]`:

| Workload | GPUs | Compute | NVLink bytes sent | NIC bytes sent | Observed step |
|---|---|---|---|---|---|
| A: 70B decode, TP = 8, batch 32 | 8 (one node) | 0.56 TFLOP | 0.147 GB | 0 | 9.5 ms |
| B: MoE training, expert parallel across 8 nodes | 64 | 400 TFLOP | 40 GB | 30 GB | 1.5 s |

Workload A also reads 20.18 GB from HBM per GPU per step; B reads 500 GB.

1. Compute each workload's compute, memory, scale-up, and scale-out lower bounds.
2. State which resource dominates each workload and which network (scale-up or scale-out) carries
   the communication that matters.
3. For each, name two pieces of telemetry that would confirm your conclusion on real hardware and
   say what values you would expect.
4. For B, propose one placement change that would shift communication from scale-out to scale-up and
   state its limit on ORION.

**Evidence required:** a table of the eight lower bounds with formula and units; the dominant
resource per workload with ceiling fraction; named metrics with expected direction/magnitude; one
placement proposal with its constraint.

### Exercise 1.3 — Role-to-skill matrix ★ · L1

Build a role-to-skill matrix for **AI Network Engineer**, **GPU Cluster Engineer**, and **AI
Infrastructure SRE** using the 0–3 scale of Section 1.8 and at least 12 skill domains. Then add a
fourth column for yourself today. For every cell where your score is ≥ 2 below the role you target,
name one chapter of this book and one concrete artifact (lab output, script, design doc) that would
close the gap.

**Evidence required:** the matrix; a written justification (one sentence) for each role's two
highest-rated and two lowest-rated domains; a gap list with chapter and artifact for each gap.

---

## Knowledge checks ★ · L1

**K1.** Give five properties that distinguish an AI training cluster from a conventional cloud fleet,
each with an ORION number.

**K2.** Why does one GPU running 10 % slow reduce the throughput of a 256-GPU synchronous training
job by about 10 %, rather than by 10 %/256?

**K3.** Convert: (a) 400 Gb/s to GB/s; (b) NVLink "900 GB/s" for an ORION GPU into a per-direction
figure; (c) a node's total backend bandwidth into GB/s per direction.

**K4.** Define prefill and decode, and state which resource typically bounds each.

**K5.** What is the per-participant send volume of a bandwidth-optimal all-reduce of *S* bytes among
*p* participants? Evaluate the factor for *p* = 4 and *p* = 8.

**K6.** What does a ceiling fraction greater than 1.0 tell you about a workload profile? What does a
ceiling fraction of 0.1 tell you?

**K7.** Why is `nvidia-smi` "GPU utilization" weak evidence that a job is compute-bound? Name a better
metric.

---

## Worked problems

### WP1 — Re-partitioning W-TRAIN ★★ · L1

Halcyon considers running W-TRAIN as TP = 4, PP = 8, DP = 8 (still 256 GPUs; each TP group occupies
half a node). For one GPU per step, compute: (a) tensor-parallel bytes sent and the NVLink lower
bound; (b) data-parallel bytes sent and the NIC lower bound; (c) pipeline bytes sent by a
middle-stage GPU and the NIC lower bound; (d) compare with the TP = 8, PP = 4 baseline of Table 1.6
and name one cost of the new layout that the ceiling model does not capture.

**Evidence required:** formula → substitution → result for each of (a)–(c), with units; a comparison
table; one named unmodeled cost with a one-sentence mechanism.

### WP2 — FP8 serving on half a node ★★★ · L1

W-INFER is redeployed with FP8 weights at TP = 4, two replicas per `HX8` node, KV cache still BF16.
For a decode step at batch 32 and mean context 2,048 tokens per replica: (a) weight and KV bytes read
per GPU; (b) memory and compute lower bounds (FP8 dense peak ≈ 1,979 TFLOP/s per GPU); (c) per-node
output tokens/s if the ceiling fraction stays 0.63, compared with BF16 TP = 8 (≈ 3,370 tokens/s per
node); (d) the arithmetic intensity at batch 32 counting weights only, versus FP8 machine balance.

**Evidence required:** all arithmetic shown; a before/after table; one sentence on what would have
to be measured to trust (c).

---

## Hands-on lab ★★ · L1 (L2/L3 extensions)

Complete the workload-characterization lab in [lab/README.md](lab/README.md): implement
`starter/workload_model.py` until `python check.py` passes, then write the one-page comparison for W01
vs W02 and a short data-quality note listing every row you rejected or flagged and why.

**Evidence required:** `check.py` output showing 9/9 PASS; the generated comparison Markdown; the
data-quality note (one line per rejected/flagged row with the root-cause hypothesis for the flaw).

---

## Troubleshooting case ★★★ · L1

One W-INFER replica (`orion-n23`) shows TPOT p95 of 19 ms while the other eleven replicas show 12 ms
`[ILLUSTRATIVE]`. Healthy p95 sits above the ≈ 9.5 ms median decode step of Section 1.9 because, under
continuous batching, some steps also carry prefill chunks of newly admitted requests, and p95 adds
scheduler jitter. Batch sizes, prompt mix, and model version are identical (the router balances
evenly). Evidence available so far:

| Signal | `orion-n23` | Other replicas (median) |
|---|---:|---:|
| `DCGM_FI_PROF_DRAM_ACTIVE` (mean of 8 GPUs) | 0.41 | 0.63 |
| `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE` | 0.05 | 0.08 |
| NVLink link state, GPU 5 (`nvidia-smi nvlink --status`) | links 0–17 `inactive` | 18 links at 26.562 GB/s |
| NVLink replay counter, GPU 2 | rising, ≈ 1/s | 0 |
| Clock-event reasons active | none | none |
| GPU temperature (max) | 71 °C | 70 °C |

1. Rank at least three hypotheses across compute, network (scale-up and scale-out), and orchestration.
2. Explain mechanistically why a problem on one GPU's links slows all eight GPUs of the replica, and
   why decode is especially sensitive to it.
3. Propose two discriminating tests, both safe on a production serving node, and the expected result
   of each under your top hypothesis.
4. Propose a safe remediation and a validation criterion.

**Evidence required:** ranked hypotheses with for/against evidence; mechanism paragraph; two tests
with expected outcomes; remediation with a measurable validation criterion; explicit statement of what
is proven versus correlated.

---

## Design challenge ★★★ · L1

Halcyon needs inference capacity for W-INFER equivalent to eight `HX8` nodes. Option A: carve eight
nodes out of ORION's training partition and share them (training jobs may use them when inference
load is low). Option B: buy a dedicated eight-node inference pool on the frontend network only (no
backend RDMA NICs). Using the chapter's trade-off criteria, recommend one option. Address: SLO risk,
utilization and cost (use $2.50/GPU-hour `[ILLUSTRATIVE]`), what the backend fabric is and is not
needed for in inference, scheduler implications (Slurm vs Kubernetes), failure domains, and what
evidence would make you change your recommendation.

**Evidence required:** a one-page recommendation with a criteria × option table, at least one
quantified argument, explicit assumptions, and a "would change my mind if…" section.

---

## Reflection and review

**R1.** ★ The ceiling model in Section 1.6 assumes peak rates and perfect overlap. List three things it
cannot capture and, for each, the measurement that would expose it.

**R2.** ★★ Build a small, dated job-posting register (≥ 5 postings across ≥ 3 employer groups) with
the fields listed in Section 1.8. What can and can't you conclude from it? Why must every
"the market requires X" claim be dated?

**R3.** ★ Which numbers in Section 1.9 are `[MODELED]`, which `[ILLUSTRATIVE]`, and which would you
need to make `[MEASURED]` before presenting the capacity-review answer to a budget owner?

**R4.** ★★ In the Section 1.11 incident, GPU utilization stayed at 96–97 %. Write the dashboard
annotation you would add so the next on-call engineer is not misled.

---

## Quick self-check (from the manuscript)

**Q1.** Why is "GPU utilization 97 %" weak evidence that a training job is compute-bound?
**Q2.** A profile claims a GPU sent 40 GB through its 400 Gb/s NIC in 0.5 s. What do you conclude?
**Q3.** On ORION, why do W-TRAIN data-parallel all-reduces never cross a spine switch?
