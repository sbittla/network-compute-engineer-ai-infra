# 2.8 — Power-cap sweep (L2): marking guide and expected shape

There is no single numeric answer; the method is graded. Sources: manuscript Section 2.6 ("Power
capping", "Throttling") and Section 2.10 Step 5 (the 570 W feed-loss limit).

**Method that earns full credit.** On a dedicated, authorized server only: record the default limit
(`nvidia-smi -q -d POWER`), then sweep from the maximum (700 W) down to ≈ 385 W (55 %) in ≈ 50 W steps
with `sudo nvidia-smi -i 0 -pl <W>`. At each step: 2 minutes of warm-up, then 5 × 60 s measurements,
sampling `nvidia-smi --query-gpu=power.draw,clocks.sm,temperature.gpu --format=csv -l 1` alongside the
workload's own throughput counter (TFLOP/s for GEMM, GB/s for a copy). Report the median and min–max (or
IQR) of the five repetitions per step, and **restore the default limit** at the end, recording that you
did. The manifest names the GPU model, driver, default limit, workload (matrix size, dtype), warm-up and
repetitions.

**Expected results.**

1. *Compute-bound GEMM:* throughput falls much more slowly than power as the limit drops, because the
   controller trades voltage and frequency, and dynamic power scales roughly with V² f. Throughput per
   watt therefore rises from the maximum and peaks somewhere mid-range, typically with a throughput
   loss far smaller than the power saving. Below the peak, clocks fall steeply and efficiency drops
   again. The learner reports the measured peak and the loss there `[MEASURED]`.
2. *Memory-bound copy:* the throughput curve is much flatter. HBM bandwidth, not SM clock, limits the
   kernel, and the GPU draws less than the cap over most of the range, so caps cost little until they
   bite on memory-subsystem power. Throughput per watt is highest at low limits.
3. *Feed-loss policy:* choose the highest limit that satisfies the feed-loss budget. For ORION that is
   **570 W** (Section 2.10: shed 1.04 kW across 8 GPUs to keep DC load ≤ 8.55 kW). Read the measured GEMM
   throughput at 570 W (say *x* % below the 700 W value) and convert it to W-TRAIN: only the
   clock-sensitive compute share of the 17.4 s step slows, so the step grows by less than *x* % (in
   Exercise 2.7 about 45 % of the step behaved as clock-scaled). Label it
   `[MODELED from MEASURED single-GPU data]` and note that collectives and other non-compute time dilute
   the effect.

**Deductions:** heavy if the server was shared or the default limit was not restored; no medians or only
one run per step; mixing `[MEASURED]` single-GPU numbers with modeled job numbers without labels.

## Hardware run (L2 harness)

The course harness (`python scripts/hw_labs.py run ch02 --device gpu`, experiment `lab/l2/experiment.py`)
measures the default-limit point of this exercise and nothing below it. It reads the enforced limit, runs
idle / FP16 GEMM / copy phases and samples `power.draw.instant`, SM clock, temperature and the
clock-event bitmask every 100 ms. On the reference laptop GPU the GEMM sits at the enforced limit with SW
Power Cap active in almost every sample and the SM clock well below the clock-table maximum. The copy
draws clearly less power and is not capped. That is the qualitative answer to question 2 at one limit,
and the reason throughput per watt must be quoted per workload. The sweep itself (questions 1 and 3) is
recorded as not runnable: it needs root on a dedicated, authorized server and a driver that allows
`nvidia-smi -pl` (not a WSL2 laptop). Accept the harness report as evidence for the default-limit step
only; the remaining steps, the plot and question 3 still need the real sweep, and question 3 stays
`[MODELED from MEASURED]`. CPU fallback: the same phases on the CPU, throughput only, power recorded as
not measurable.
