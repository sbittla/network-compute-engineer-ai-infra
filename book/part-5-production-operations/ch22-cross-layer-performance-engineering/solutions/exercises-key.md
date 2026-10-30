# Chapter 22 — Answer Key (INSTRUCTOR ONLY)

Values are `[ILLUSTRATIVE]` or, for the lab, `[SIMULATED]` from the committed bundle (seed 2214). Every
calculation below was checked twice; the lab numbers are reproduced by
`python solutions/lab/regression_lab.py`.

---

## Knowledge checks

**K1.** `T_step = T_compute + T_comm,exposed + T_bubble + T_data,exposed + T_host + T_ckpt,amortized`.
Exposed comm: Nsight Systems NCCL ranges on the timeline (per kernel), or framework per-rank
collective-wait timers (per step). Data wait: the loop timer around fetching the next batch (`data_wait`
per step); supporting: dataloader worker stats, storage client latency, CPU iowait.
*Marking:* 2 pts equation (all six terms), 1 pt per correct source with grain. *Common mistake:* naming
NIC throughput as a measure of exposed comm — throughput says nothing about overlap.

**K2.** `GPU-Util` / `DCGM_FI_DEV_GPU_UTIL` is the fraction of the sample period during which at least one
kernel was executing; NCCL kernels spinning while waiting for peers count as "utilised". Better:
`DCGM_FI_PROF_SM_ACTIVE` (fraction of SMs with resident warps), `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE`,
SM clock plus clock-event reasons, and timeline breakdown of compute vs communication kernels.
*Common mistake:* "100 % util means compute-bound".

**K3.** A minority of jobs is badly affected while most are near baseline: a placement-, node-, or
dataset-specific cause rather than a fleet-wide change. Unchanged p99 suggests a steady slowdown on those
jobs, not intermittent stalls. First partition: by any job attribute that differs within the window and
maps to a mechanism — e.g., "TP group spans nodes" (placement records) or "ran on upgraded nodes".
*Marking:* interpretation 2 pts, concrete partition + hypothesis 2 pts.

**K4.** A discriminating test is one for which competing hypotheses predict different outcomes.
Example: partition after-period jobs by whether any TP group spans two nodes. H-placement predicts a large
gap between the groups; H-network (fabric congestion) predicts that all multi-node jobs slow similarly,
so no gap aligned with TP span. Non-example: "look at the fabric dashboard" — TP-split jobs, GDR-off jobs,
and genuine congestion all raise backend traffic or counters, so every hypothesis predicts "something odd".

**K5.** The period indicator absorbs any shift common to all after-period jobs (e.g., the container
rebuild). Without it, that shift is forced onto whichever factor has the highest exposure; in the lab,
dropping `after` raises the driver effect from 0.90 s to 1.07 s, the storage effect from 1.40 s to
1.57 s, and TP split from 8.96 s to 9.18 s (the common shift must go somewhere).
*Marking:* role 2 pts; concrete misattribution 2 pts.

**K6.** `E_strong(N) = T(N0)·N0 / (T(N)·N)` (fixed global problem). `E_weak(N) = X(N) / ((N/N0)·X(N0))`
with X in tokens/s (per-GPU work fixed). 64 → 256 GPUs for W-TRAIN is weak scaling: DP grows 2 → 8 and the
global batch grows 256 → 1,024 sequences, so per-GPU work is constant.

**K7.** Survivorship bias: analysing only jobs that completed (or only "healthy" runs) excludes jobs that
failed, which are often the ones most affected. Placement regressions push TP traffic onto the fabric,
making split jobs both the slowest and the most likely to hit collective timeouts; dropping failed jobs
removes the strongest evidence and shrinks the measured effect (lab: TP share falls from 64.7 % to 61.4 %,
headline from +23.2 % to +21.9 %).

**K8.** (1) Confounding: load, job mix, and other changes vary over the rollback period, so the
before/after comparison mixes the rollback with everything else that changed; it also destroys the
natural experiment (half upgraded, half not) that was answering the question for free. (2) Poor
information per cost and risk: a rollback answers one leaf slowly (days) at high cost (drains, reboots)
and with production risk, while offline partitions answer several leaves in minutes.

---

## Worked problems

### W1 — attribution with an interaction

a. After mean = (4×17.6 + 3×24.8 + 2×19.4 + 1×28.2)/10 = (70.4 + 74.4 + 38.8 + 28.2)/10 = 211.8/10 =
**21.18 s**. Δ = 21.18 − 17.40 = **3.78 s**; 3.78/17.40 = **+21.7 %**.

b. Period shift = 17.6 − 17.40 = **0.20 s**. Effect P (at S = 0) = 24.8 − 17.6 = **7.20 s**.
Effect S (at P = 0) = 19.4 − 17.6 = **1.80 s**. Interaction = 28.2 − 17.6 − 7.2 − 1.8 = **1.60 s**.

c. Exposures after (before all 0): P = (3 + 1)/10 = 0.4; S = (2 + 1)/10 = 0.3; P×S = 1/10 = 0.1.

| Term | Effect (s) | Δ exposure | Contribution (s) | Share |
|---|---|---|---|---|
| Period shift | 0.20 | 1.0 | 0.20 | 5.3 % |
| P | 7.20 | 0.4 | 2.88 | 76.2 % |
| S | 1.80 | 0.3 | 0.54 | 14.3 % |
| P × S | 1.60 | 0.1 | 0.16 | 4.2 % |
| **Total** | | | **3.78** | **100 %** |

Check: 0.20 + 2.88 + 0.54 + 0.16 = 3.78 ✓ (shares 0.20/3.78 = 5.29 %, 2.88/3.78 = 76.19 %,
0.54/3.78 = 14.29 %, 0.16/3.78 = 4.23 %).

d. mean(P=1) = (3×24.8 + 28.2)/4 = 102.6/4 = 25.65; mean(P=0) = (4×17.6 + 2×19.4)/6 = 109.2/6 = 18.20;
naive P = **7.45 s**. mean(S=1) = (2×19.4 + 28.2)/3 = 67.0/3 = 22.33; mean(S=0) = (4×17.6 + 3×24.8)/7 =
144.8/7 = 20.69; naive S = **1.65 s**. They differ from (b) because each naive difference averages over an
unbalanced mix of the other factor (P is present in 3/7 = 43 % of S = 0 jobs but 1/3 = 33 % of S = 1 jobs,
pulling naive S down) and folds in part of the interaction (pulling it up). Here the biases partly
cancel; in the lab bundle they do not (naive storage difference ≈ −0.55 s).

e. Note first that the *simple* slack model predicts a **negative** interaction (a longer TP-split step
gives the loader more slack and hides recalls — exactly what the lab bundle shows). A positive interaction
therefore needs another mechanism, e.g., CPU contention: TP-split jobs move TP traffic onto the NICs, so
NCCL's network proxy threads consume more host CPU on the same NUMA node as the dataloader workers,
raising batch production time so that recalls are exposed *more*. Evidence to check: `pidstat -u -t 1`
per-thread CPU for proxy threads and loader workers, NUMA placement (`numastat -p`), and producer time
per batch. *Marking:* full marks only if the answer either gives a mechanism with evidence or notices the
sign conflict with the slack model.

### W2 — scaling efficiency and detectability

a. Per-GPU work constant, so `E_weak = T(64)/T(N)`:
- 128 GPUs: 2,097,152 / 17.62 = 119,021 tokens/s (929.9 per GPU); E = 17.38/17.62 = **98.6 %**.
- 256 GPUs: 4,194,304 / 17.90 = 234,318 tokens/s (915.3 per GPU); E = 17.38/17.90 = **97.1 %**.
(64 GPUs: 1,048,576 / 17.38 = 60,332 tokens/s, 942.7 per GPU.)

b. Straggler model with σ = 0.5 s: 16 nodes: (1.77 − 1.42) × 0.5 = **0.175 s** of the 0.24 s gap
(remaining 0.065 s); 32 nodes: (2.07 − 1.42) × 0.5 = **0.325 s** of the 0.52 s gap (remaining 0.195 s).
DP exposure explains part of each remainder: ring traffic 4.38 → 6.56 → 7.66 GB per GPU at DP 2 → 4 → 8 is
0.097 → 0.146 → 0.170 s at 45 GB/s; only ≈ 70 ms hides behind the last micro-batch's backward pass, so
exposure is ≈ 0.03 → 0.08 → 0.10 s, i.e. +0.05 s (16 nodes) and +0.07 s (32 nodes), leaving ≈ 0.015 s
and ≈ 0.125 s unexplained.

c. MDE(n = 5) = 2.8 × 0.11 × √(2/5) = 2.8 × 0.11 × 0.632 = **0.195 s** > 0.15 s, so **no**, 5 runs per arm
cannot reliably detect it. Required n: n = 2 × (2.8 × σ / δ)² = 2 × (0.308 / 0.15)² = 2 × 2.053² = 2 × 4.216
= 8.43 → **9 runs per arm** (interleaved, same nodes).
*Common mistakes:* using strong-scaling efficiency; forgetting the √2 for two arms; rounding n down.

---

## Lab key (L1)

### Expected results (reference implementation, committed bundle)

| Quantity | Value |
|---|---|
| Rows after cleaning | 8,990 (9,514 raw − 44 duplicates − 480 warm-up rows) |
| TP-split jobs | 41102, 41107, 41109, 41112, 41114, 41117, 41123 |
| Exposure counts | after 24, tp_split 7, driver_new 12, storage_new 14, alert_node 6, tp_x_storage 3 |
| Mean step, before → after | 17.38 s → 21.42 s (+4.04 s, **+23.2 %**) |
| Median of per-job means | 17.42 s → 19.70 s (**+13.1 %**) |
| Effects ± SE (s/step) | after +0.34 ± 0.09; tp_split +8.96 ± 0.10; driver_new +0.90 ± 0.07; storage_new +1.40 ± 0.07; alert_node −0.05 ± 0.09; tp_x_storage −1.31 ± 0.15; R² = 0.998 |
| Shares of the 4.04 s (interaction as its own row; ± classical SE) | TP split 64.7 % ± 0.7 pp; capacity tier 20.2 % ± 1.1; R570/GDR 11.2 % ± 0.9; common shift (period indicator, not attributable to a named change) 8.3 % ± 2.2; TP × storage interaction −4.0 % ± 0.5; ECC alert −0.3 % ± 0.6; residual 0. Sum 100 %. |
| Equal-split alternative | Interaction split equally between parents: TP 62.7 %, storage 18.1 % (others unchanged) |
| HC3-robust share SEs | common shift 1.7 pp, TP 0.5, driver 1.1, storage 1.1 |
| Observed-event 95 % (conditional on exposure, HC3) | common shift 8.3 ± 1.96 × 1.7 ≈ 5.0–11.6 % (classical ≈ 4.0–12.6 %) |
| Future-sweep bootstrap 95 % (2,000 resamples, seed 22; 116 rank-deficient dropped; resamples exposure) | common shift 4.2–14.2 %; TP 42–78 %; storage 11–33 %; driver 6–19 %: shares depend strongly on which jobs were exposed, effects much less |
| Step-weighted (GPU-hour) change | 17.38 → 21.27 s, +22.3 % (failed short job down-weighted) |
| Storage cross-check | data-wait delta (TP-packed jobs) +1.46 s vs coefficient +1.40 s → consistent |
| Test ranking | T3 (3.200), T1 (1.800), T2 (1.400), T4 (1.200), T8 (0.250), T6 (0.117), T7 (0.075); rejected T5, T9 |

### Ground truth encoded by the generator (do not share with learners before grading)

Base 17.35 s + data wait; after-period shift +0.20 s (CHG-7802, the container rebuild); TP split +8.90 s;
driver (GDR disabled on R570 nodes) +1.00 s for any job touching orion-n17..n32; capacity-tier recalls with
probability 0.10 per step, 10–18 s each (≈ +1.45 s per step) — but only 10 % of each recall is exposed on
TP-split jobs (true interaction ≈ −1.26 s); ECC alert effect 0. Noise: per-step σ 0.30 s, per-job σ 0.10 s.
Estimates recover the truth within about 1.5 SE.

### Planted flaws and what they teach

| # | Flaw | Where | Effect if missed |
|---|---|---|---|
| 1 | Log-shipper replay: the 22 stall steps of job 41105 appear three times (44 extra rows) | `step_log.csv` | Job 41105 mean 19.29 → 21.59 s; p99 inflated; storage effect overstated |
| 2 | Warm-up steps 0–9 (+30 s decaying; +4 s data wait at step 0) | `step_log.csv` | Before mean 17.38 → 17.70 s; short jobs (the failed one) look worse |
| 3 | Failed TP-split job 41114 (60 usable steps, NCCL timeout) | `jobs.csv` status FAILED | Dropping it: headline +21.9 %, TP share 61.4 % — survivorship bias |
| 4 | Inventory shows **current** driver; before-period jobs on orion-n17..n32 ran R550 | `node_inventory.csv` | Non-time-aware flag: driver effect 0.35 s, after shift 0.93 s, alert −0.47 s — wrong on three factors |
| 5 | Red-herring alert: ECC SBE 140–160 per job-node on orion-n13 (no DBE, no remap) | `alerts.csv`, `node_metrics.csv` | Alert-led diagnosis; correct verdict: effect −0.05 ± 0.09 s, ruled out |
| 6 | Confounding: TP-split is over-represented among hot-tier jobs (40 % vs 21 %) and hides stalls | design | Naive storage difference ≈ −0.55 s ("the move helped") |
| 7 | True TP × storage interaction | design | Additive-only model: storage 1.03 s, after 0.73 s, alert −0.43 ± 0.14 s (spuriously "significant") |
| 8 | `BackendLinkFlap` on 2026-10-09, *before* the window, port clean since | `alerts.csv` | Time-ordering check: cannot explain an after-window change |
| 9 | Change validations that did not test the data path: driver "dcgmi diag pass" (no GDR check); storage "bulk read 40 GB/s from one client" (bandwidth, not tail latency) | `change_log.yaml` | Teaches why validation must exercise the mechanism the change touches |

### Marking guidance

Award the hygiene points only if the learner *reports* what each rule removed (44 rows, 480 rows, 0 jobs).
A learner who used the additive-only model but noticed the alert's implausible negative effect and
investigated earns most of the effect-estimation credit; one who reports "the ECC alert speeds jobs up"
without comment loses it. The report must not contain causal words ("because", "caused by") in Measured
facts.

---

## Troubleshooting case T1 — periodic stalls

a. **Tree** (root: median +0.6 s, periodic +6–9 s collective-wide stalls; data wait flat; wait unimodal):
- *Physical-layer degradation on one link → RoCE loss → retransmission.* Fingerprint: errors on one port
  only; NIC `out_of_sequence` (NAK-recovered losses) and `local_ack_timeout_err` (timeout-recovered losses)
  rising on that NIC; all ranks stall together because the collective waits on one flow. **Matches.**
- *Fabric congestion / PFC storm.* Fingerprint: ECN marks and PFC pauses rising on many ports, correlated
  with load; no CRC/FEC errors. Contradicted by port-local errors.
- *Straggler compute.* Fingerprint: bimodal wait, clocks/thermal reasons. Contradicted (unimodal, clean
  clocks).
- *Storage or checkpoint stall.* Fingerprint: data wait up or periodicity equal to checkpoint interval.
  Contradicted (data wait flat; 30–50-step irregular period).
- *Host jitter on one node (GC, IRQ storm).* Fingerprint: one rank late; timeline gaps on one host.
  Possible but the NIC counters point elsewhere.

b. **Ranking** (score = info / (cost × risk)):

| Test | Info | Cost (h) | Risk | Score |
|---|---|---|---|---|
| Correlate long-step timestamps with increments of `local_ack_timeout_err` on orion-n15 `mlx5_3` and FEC uncorrectable on orion-be-leaf-r3 Ethernet28 (existing telemetry) | 0.8 | 0.5 | low | 1.6 |
| Read module diagnostics on both ends: host `ethtool -m <rail-3 netdev>` (DOM Rx/Tx power), switch transceiver DOM (vendor CLI) | 0.6 | 0.5 | low | 1.2 |
| On a drained orion-n15 and a peer: `ib_write_bw -d mlx5_3 --report_gbits` on rail 3 plus error counters during the run | 0.7 | 3 | medium | 0.117 |

c. **Root cause and chain.** The NIC3 optic on orion-n15 (reseated three days ago; likely contaminated or
damaged connector) has a marginal optical budget → high pre-FEC bit-error rate (FEC corrected codewords
~500× other ports) → some codewords uncorrectable (312 per 10 min) → frames fail CRC and are dropped
(297 in-errors; host `rx_crc_errors_phy`, `rx_symbol_err_phy` rising) → RoCE packets lost on reliable-
connected QPs. Losses followed by more packets are detected as out-of-sequence and recovered by NAK and
go-back-N retransmission (small delays every step → median +0.6 s); losses of the *last* packets of a
message are recovered only by the ACK timeout. The case states NCCL 2.23+, where the default
`NCCL_IB_TIMEOUT` is 20: 4.096 µs × 2²⁰ ≈ 4.3 s, so one or two timeouts on the critical path produce the
6–9 s stalls. On NCCL ≤ 2.22 the default is 18 (4.096 µs × 2¹⁸ ≈ 1.07 s), and 6–9 s would mean several
consecutive retries `[VENDOR-SPEC, 2026-10]`.

d. **Fix.** Fabric team, under a change ticket: at the job's next checkpoint boundary, cordon orion-n15
(ORION has no spare node, so the job pauses or restarts at reduced DP from checkpoint by Training Infra's
decision), clean/replace the rail-3 optic (both ends inspected), then run acceptance: link up at
400 Gb/s, FEC corrected codewords back to baseline (1–4e6 per 10 min), zero uncorrectable and zero CRC over
a 1 h soak, `ib_write_bw` at ≥ 90 % of line rate on rail 3, `all_reduce_perf` two-node busbw matching
fleet baseline. Return to service through the lifecycle workflow (Chapter 16). **Validation:** 5 × 100-step
windows with median 17.9 ± 0.1 s, no step > 20 s in 1,000 consecutive steps, `local_ack_timeout_err` flat.
*Marking:* deduct if the plan touches switch configuration, raises `NCCL_IB_TIMEOUT` to "fix" it (masks the
fault), or reseats optics on a live job without a ticket.

---

## Design challenge D1 — continuous regression detection

Reference answer (accept well-argued alternatives):

| Option | Detection time | GPU cost | False positives | Causal strength |
|---|---|---|---|---|
| A. Daily dedicated canary (one 64-GPU W-TRAIN ablation, 1 h, pinned placement) | ≤ 24 h | 64 GPU-h/day of 256 × 24 = 6,144 → **1.04 %** | Low (controlled) | Strong for the canary config; misses placement/dataset effects that canaries never exercise |
| B. Mine production jobs (natural-experiment pipeline joining step logs, placement, time-aware inventory, change calendar) | Hours after enough jobs | ≈ 0 | Medium (confounding, small cells) | Moderate; covers real placements and datasets |
| C. Hybrid: B continuously, A daily, plus an on-demand reserved A/B to confirm | ≤ 24 h | ≈ 1 % + occasional reservations | Low after confirmation | Strong |

Detectability for A: a 3 % regression at 17.4 s is 0.52 s; with σ = 0.11 s, n = 2 × (2.8 × 0.11/0.52)² =
2 × 0.351 = 0.70, so even one run per day per arm detects it in principle — but day-to-day drift means you
should compare against a rolling 7-day baseline (n = 7). Recommend **C**, with alert thresholds of
baseline + max(3σ, 3 %) and automatic attribution reports in the Section 22.9 format.

---

## Reflection

**R1.** The 0.34 ± 0.09 s common shift (8.3 % ± 1.7 pp HC3 for this event; future-sweep bootstrap 4–14 %) could be: (i) the container rebuild CHG-7802 (e.g., a library
change despite "framework unchanged"); (ii) an unmodeled interaction or a non-linear straggler effect;
(iii) a time-varying environmental factor (fabric neighbours, facility temperature) coincident with the
window. Separate (i) by an A/B of old vs new container digest on reserved nodes; (ii) by fitting
additional interaction terms and inspecting residuals by job type; (iii) by checking neighbour load and
facility telemetry for the after period.

**R2.** R² measures how well indicators reproduce per-job means *in this sample*; it says nothing about
direction of causation, omitted variables correlated with the indicators, or whether a mechanism exists.
The additive-only model also has R² ≈ 0.995 yet gives a spurious negative ECC "effect".

**R3.** Excluding failed job 41114: headline +21.9 % (vs +23.2 %), TP share 61.4 % (vs 64.7 %), common-shift share
8.9 %. The *ranking* of causes, the alert verdict, and the storage cross-check do not change. The
p99-based and "fraction of jobs hurt" statements weaken.

**R4.** The L1 bundle shows a correlation between R570 nodes and slower jobs, a host bounce-copy metric
(0.4 → 9.5 GB/s on upgraded nodes after the window), illustrative NET channel lines without `/GDRDMA`, and
an `lsmod` check. It cannot show how much bandwidth was lost. L2: on one upgraded node, confirm the
peer-memory module is absent and that DMA-BUF is unavailable for that kernel/driver/RDMA stack (otherwise
GDR could still work without the module). L3: `all_reduce_perf` between an R550
and an R570 node with and without the module loaded, ≥ 5 runs, busbw median and spread, and the
`via NET/IB/x/GDRDMA` channel lines, recorded with a manifest.

---

## Outline-mandated exercises

**O1.** (a) As in the lab key. (b) Corroboration table:

| Cause | Direct evidence (lab bundle) |
|---|---|
| TP split | Backend tx per node 6.06 → 37.93 GB/s; SM active 0.57 → 0.40 (after, split vs not) |
| Storage tier | Data wait +1.46 s/step on TP-packed jobs; CPU iowait 1.52 % → 6.03 %; per-job p99 18.8 → 35.0 s while p50 barely moves (18.17 → 18.24 s) |
| Driver / GDR | Host bounce copy 0.4 → 9.5 GB/s on orion-n17..n32 after the window only; `nccl_init_sample.log`: channel lines `via NET/IB/0` (no `/GDRDMA`) on orion-n17 vs `via NET/IB/0/GDRDMA` on orion-n09, and empty `lsmod \| grep nvidia_peermem` on orion-n17; inventory `peermem_module_loaded = no`. Caveat: valid only because DMA-BUF is unavailable on these nodes `[VENDOR-SPEC, 2026-10]` |
| ECC alert (ruled out) | SBE 0.7 → 152 per job-node on orion-n13, temperatures unchanged (67.4 → 68.1 °C), effect −0.05 ± 0.09 s |

(c) With both interactions: tp_x_storage −1.30 ± 0.15 s (≈ 8.7 SE, predicted by the slack model: keep);
tp_x_driver +0.03 ± 0.13 s (negligible: drop). The model with the single tp_x_storage term is defensible;
an additive-only model is not (it distorts storage, after, and alert estimates).

**O2.** Tree as manuscript Figure 22.2, extended with the BackendLinkFlap leaf (ruled out by time
ordering) and the container leaf. Ranking as in the lab key. Example learner additions: "Diff container
image package lists, old vs new digest" (info 0.4, 0.5 h, low, offline → 0.8, ranks between T4 and T8);
"Per-rank data-wait distribution for capacity-tier jobs to test the slack model" (info 0.5, 0.25 h, low →
2.0, ranks second). Rejected: T5, T9 (high-risk production). Then re-score after each result: once T3 shows the tier gap, T8's information value drops (≈ 0.2 → score 0.10, below T6); once T1 shows the TP-span gap, T7 becomes confirmation only and is justified only before a fleet-wide placement change.

**O3.** A model report: Measured facts (headline, median, hygiene, factor table, direct measurements);
Inferred causes with the full row set (TP split 64.7 %, capacity tier 20.2 %, TP × storage interaction −4.0 %, R570/GDR
11.2 %, common shift 8.3 %, ECC −0.3 % — sums to 100 %; equal-split alternative TP 62.7 %, storage 18.1 %);
Remaining uncertainty (common shift 8.3 % ± 1.7 pp HC3; future-sweep bootstrap 4–14 %; interaction assumptions, natural-experiment limits); Recommended
changes: (1) restore TP-packed placement for multi-node jobs — predicted −9.0 s on affected jobs, canary
one job, MDE at n = 5: 0.19 s, abort if TP groups span nodes in placement records; (2) load the peer-memory
module on R570 nodes (drained, per Chapter 16) — predicted −0.9 s on affected jobs, validate with `/GDRDMA` on NET
channel lines and the L3 busbw test; (3) four dataloader workers or move hot datasets back — predicted
−1.2 to −1.4 s on TP-packed capacity-tier jobs. *Marking:* deduct for any causal language in Measured facts,
unlabelled numbers, or a recommendation with no predicted effect or abort condition.
