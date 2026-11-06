# Exercise 2.8 — Power-cap sweep on one GPU server

**Difficulty:** ★★★ · **Tier:** L2 · **Type:** hands-on-lab · **Kind:** written · **Points:** 20

## Prompt

<!-- prompt:start -->
> **Safety:** Only on a dedicated server you are authorized to reconfigure. Restore default power
> limits afterwards and record that you did.

On one GPU, run a fixed workload (for example a large BF16 GEMM loop or an approved burn-in tool) at
power limits from the maximum down to roughly 55 % of it in about 50 W steps (`sudo nvidia-smi -i 0
-pl <W>`). At each step: 2-minute warm-up, then 5 repetitions of a 60-second measurement, sampling
`nvidia-smi --query-gpu=power.draw,clocks.sm,temperature.gpu --format=csv -l 1`. Plot throughput,
average power, and throughput per watt against the limit.

1. At what limit does throughput per watt peak? How much throughput is lost at that point?
2. Repeat with a memory-bound workload (large element-wise copy). How does the curve change, and why?
3. Using your curve, what fleet-wide limit would you propose as ORION's feed-loss policy
   (Section 2.10), and what would it cost the W-TRAIN step time if it were applied continuously?

**Evidence required:** filled-in `lab/manifest.yaml` copy (GPU model, driver, default limit, workload
definition, warm-up, repetitions); raw CSV; plot; median and spread per step; explicit
`[MEASURED]` versus `[MODELED]` labels for the answer to question 3.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 2 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the assumptions of the chapter's Sections 2.2–2.10.
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Put every deliverable in [`outputs/`](outputs/):

- `outputs/manifest.yaml`: filled-in copy of `lab/manifest.yaml`
- `outputs/sweep.csv`: raw per-second samples for every limit and repetition
- `outputs/sweep.png`: throughput, power and throughput per watt against the limit
- `outputs/report.md`: median and spread per step and answers to questions 1 to 3 with `[MEASURED]`/`[MODELED]` labels

Answer in prose. Give any number you use with its unit and an evidence label (`[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`).

**Hardware run (course harness).** From the repository root, `python scripts/hw_labs.py run ch02 --device
gpu` measures the GPU at its *default* power limit: idle, a compute-bound GEMM and a memory-bound copy,
with power, clocks and clock-event reasons sampled every 100 ms. It writes `lab/l2/results/gpu-<model>/`.
It never changes the limit, so it gives you the first point of the sweep and the compute- versus
memory-bound contrast of question 2, not the sweep itself. If you use it, copy its `report.md` to
`outputs/l2_baseline_report.md`. Without a GPU, `--device cpu` runs the CPU fallback automatically
(throughput only, no power). The harness builds and runs a Docker image, so Docker must be running.