# Capstone C — Instructor Grading Guide

INSTRUCTOR ONLY. Removed from the student edition by `scripts/make_student_release.py`, together with
`starter-kit/tools/`.

## 1. What the generator does

Step time = compute (≈ 17.39 s per replica at 40 % MFU `[MODELED]`) × (1 + the slowest of the nodes'
N(0, 1.2 %) deviations), plus exposed DP all-reduce, plus exposed PP send/recv, all × a run offset
N(0, 0.4 %) × step noise.

- **DP exposure** follows docs/VERIFIED_FACTS.md: with PP = 4, only the last micro-batch's backward can
  hide the DP collective, a ≈ 70 ms window, so exposed = max(0, T_DP − 0.07 s).
- **Baseline:** inter-node bandwidth is 2.5 GB/s per GPU (≈ 20 GB/s busbw per node over NCCL's TCP
  socket transport on the 2 × 200G frontend). At DP = 8, T_DP = 7.66 GB / 2.5 GB/s = 3.06 s, so ≈ 2.99 s
  is exposed.
- **`ib_gdr`:** 40 GB/s per rail. T_DP = 0.191 s, so 0.121 s is exposed.
- **`ib_gdr_bucket`:** the window is 85 ms, an `[ILLUSTRATIVE]` +15 ms for fewer, larger buckets.
- **PP send/recv:** half is exposed `[ILLUSTRATIVE]`.
- **Warm-up:** the first five steps of each run (and after a restart) carry multipliers 3.1, 1.35, 1.18,
  1.08 and 1.03.
- **Volume:** 8 repetitions per variant × scale, 96 runs in total.
- **Modeling choice, PP exposure (`[ILLUSTRATIVE]`, deliberate per capstone):** C exposes 50 % of PP
  send/recv, while Capstone A's design model treats 1F1B send/recv as fully hidden. C's choice is what
  makes the baseline ≈ 1 % slower at 32 GPUs (DP = 1); under A's choice that difference would vanish.

## 2. Planted issues

| Issue | Where | Correct handling |
|---|---|---|
| Warm-up in every run | steps 0–4 | Exclude by a stated policy; show why 5 (step 0 ≈ 3× steady) |
| Restart mid-run | r0419 (baseline, 128 GPUs, rep 3): steps 0–41, then 36–59 | Detect repeated step indices; exclude the run (or drop both warm-ups and justify it) |
| Environment drift | r0444 (ib_gdr, 64 GPUs, rep 4): image `2026.09.3`, NCCL 2.21.5 | Exclude: violates one-variable-at-a-time |
| Straggler with a documented cause | r0458 (ib_gdr, 256, rep 2): median +7.1 %; note quantifies the throttle (SW thermal slowdown in 100 % of sampled steps, SM ≈ 1,710 vs ≈ 1,830 MHz, −6.6 %) | Exclude as an outlier with its cause; show results both ways |
| Statistical outlier without a cause | r0421 (baseline, 128, rep 5) | Flagged only by the MAD rule (baseline step noise σ 3.5 %). A strong submission reports it, shows the conclusions do not change if it is kept, and does **not** invent a cause |
| Non-significant "optimization" | ib_gdr → ib_gdr_bucket | Not significant at any scale after Holm (raw p 0.09–0.63) |
| Multiple comparisons | 2 comparisons × 4 scales = 8 tests | Holm (or Bonferroni) across the family; state the statistic (difference of means of run medians) |
| No warm-up policy recorded | manifests: `none-recorded` | Call out the manifest gap; define the policy |
| Units | profile in ms, runs in s | Convert explicitly |
| No 8-GPU training point | design | Explain the memory reason; use intra-node nccl-tests as the 8-GPU evidence |
| NCCL log wording | `nccl_debug_*.log` | `[ILLUSTRATIVE]`, wording varies by version. The evidence is `Using network …` and the `/GDRDMA` channel suffix |

## 3. Reference results (`[SIMULATED]`)

| Variant | 32 | 64 | 128 | 256 |
|---|---|---|---|---|
| baseline median step (s) / E | 17.78 / 1.000 | 19.61 / 0.907 | 20.61 / 0.863 (6 runs) | 21.12 / 0.842 |
| ib_gdr | 17.58 / 1.000 | 17.72 / 0.992 (7 runs) | 17.89 / 0.983 | 17.95 / 0.979 (7 runs) |
| ib_gdr_bucket | 17.60 / 1.000 | 17.76 / 0.991 | 17.83 / 0.987 | 17.93 / 0.982 |

baseline → ib_gdr speedup: 1.011 at 32, 1.107 at 64, 1.152 at 128, 1.176 at 256 (bootstrap CI at 256 ≈
[1.169, 1.185]). Raw exact p ≤ 0.0003, Holm-adjusted ≤ 0.0019 across the 8 tests, so all four are
significant. With 8 versus 7 runs the smallest attainable p is 1/6,435 ≈ 0.00016. With the original 5
versus 4 it would be 1/126 ≈ 0.008, and Holm over 8 tests (8 × 0.008 = 0.063) could never reach 0.05.
That is why the design uses 8 repetitions. ib_gdr → ib_gdr_bucket: speedups 0.998–1.003, Holm p ≥ 0.34.
Including all four excluded runs leaves the 256-GPU speedup at 1.176 (CI [1.167, 1.184]).

Why the baseline is ≈ 1 % slower even at 32 GPUs (DP = 1): PP send/recv also rides the socket transport.
That is 1.07 GB per boundary per direction at 2.5 GB/s ≈ 0.43 s, half of it exposed, against ≈ 0.01 s on
IB. Eight repetitions resolve that ≈ 0.2 s effect.

Profile at 256 GPUs: exposed communication is 15.3 % of the baseline step (3,207 of 21,028 ms) versus 0.8 %
for ib_gdr (135 ms). Baseline `memcpy_dtoh_htod` busy ≈ 1,921 ms per step: host bounce buffers, the
signature of a host-staged path.

nccl-tests at 8 GiB, busbw (algbw):

| GPUs | Variant | busbw | algbw | Reading |
|---|---|---|---|---|
| 8 (one node) | both | ≈ 366–372 GB/s | ≈ 209–213 GB/s | A healthy plain ring (≈ 0.80–0.85 × 450 GB/s busbw; the ≈ 257 GB/s ceiling applies to **algbw**). Near 450 GB/s busbw would imply NVLS |
| 16 (two nodes) | baseline | ≈ 20 GB/s | ≈ 11 GB/s | Socket transport |
| 16 | ib_gdr | ≈ 361 GB/s | ≈ 192 GB/s | ≈ 45 GB/s per rail (busbw ÷ 8) against 50 GB/s line rate |

## 4. Dimension expectations

| Dimension | Exemplary | Proficient | Developing | Insufficient |
|---|---|---|---|---|
| Framing (10) | Policies fixed before results; weak scaling justified; exposure model stated | Policies stated | Implicit | None |
| Correctness (20) | Bytes, data paths, transport mechanism right; busbw vs algbw distinguished; DP window model | Minor slip | Mechanism vague ("network slow") | Wrong mechanism |
| Implementation (15) | 12/12; harness JSON + manifest; reproducible | 12/12 | 8–11 | < 8 |
| Measurement (20) | All 4 exclusions with reasons and both-ways sensitivity; exact p with the statistic stated; Holm across 8 tests; CIs; bucket change reported as null | Raw p without correction, or no sensitivity | Means only, no spread | Simulated or proxy timings presented as GPU measurements: cap at 40 % |
| Reliability/security/ops (15) | Launcher preflight on transport (runbook template); device-plugin policy; regression alert on E(N) | Preflight only | Generic | None |
| Judgment (10) | Intra- vs inter-node discrimination; slowest-node effect; does not invent a cause for r0421 | Sound | Single hypothesis | Wrong |
| Communication (10) | One-page story with CIs | Clear | Dense | Disorganized |

## 5. Common failure patterns

1. Averaging all 60 steps, so warm-up inflates every mean by ≈ 4 %.
2. Keeping r0419, whose duplicated steps and second warm-up bias the baseline at 128 GPUs.
3. Eight uncorrected tests at α = 0.05, or declaring the bucket change "a win at 128 GPUs" (raw p 0.09).
4. Citing a GDR "enabled" line instead of the channel-line `/GDRDMA` suffix (docs/VERIFIED_FACTS.md).
5. Confusing busbw and algbw: calling ≈ 240 GB/s busbw "healthy" on one node (it is ≈ 35 % low for a
   ring), or reading multi-node busbw per node instead of per rail.
6. Modeling DP exposure as a fixed overlap percentage when PP leaves only a ≈ 70 ms window.
7. Presenting the laptop harness timing as anything other than CPU-proxy evidence.

## 6. Viva questions

1. Why is the baseline ≈ 1 % slower even at 32 GPUs, where there is no data parallelism?
2. With 5 versus 4 runs, what is the smallest exact permutation p? Could any result survive Holm over
   8 tests? How did that shape the campaign design?
3. What would `ibv_devinfo` print inside the baseline container, and why is this a platform defect rather
   than an NCCL tuning problem?
4. ib_gdr loses ≈ 2.1 % efficiency at 256 GPUs. Split it between exposed DP time (max(0, 0.191 − 0.07) =
   0.12 s ≈ 0.7 %) and the slowest-of-32-nodes effect.
5. 8-GPU busbw is 370 GB/s, but someone quotes "257 GB/s ceiling". Reconcile the two numbers.
