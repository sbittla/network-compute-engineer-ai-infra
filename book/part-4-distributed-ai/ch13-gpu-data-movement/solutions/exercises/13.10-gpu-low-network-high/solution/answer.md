# 13.10 — GPU utilization low, network utilization high (O2): worked solution

Data are the lab bundle `[SIMULATED]` (64 ranks on `orion-n17`…`orion-n24`, 60 steps). Values are from
`solutions/lab/telemetry_diag.py` and the checker's solution report. Method: Section 13.9 (robust z with
threshold 6, onset from three consecutive flagged steps, attribution with independent evidence).

| Steps | Verdict | Independent evidence |
|---|---|---|
| 0–19 | **Synchronization caused by data imbalance** on rank 12 | Rank 12 compute robust z ≫ 6 from step 0 (step 10: slowest rank 12, ratio 1.294). Its **tokens are +31 %** while clocks, temperature and power are normal. Wait ≈ 172 ms per rank on the others. Transfer stays at its 120 ms baseline. Burst NIC rate ≈ 359 Gb/s (near line rate). |
| 20–29 | Same, **plus a thermal straggler, rank 37**, hidden behind rank 12 | Rank 37 compute flagged from step 20 (z = 14.4 at step 40). SM clock **−22 %**, 90 °C, clocks-event reason `sw_thermal_slowdown`, **tokens normal**. Step time unchanged because max(rank 12, rank 37) is unchanged. |
| 30–59 | Adds **communication-bound** degradation on **rail 2** | Transfer time **120 → 198 ms** for every rank. Retransmissions ≈ 3,200 per step on local index 2 on every node versus ≈ 1 elsewhere. Burst NIC rate falls **359 → 222 Gb/s**. Rail 2 flagged, onset step 30. SM active 58.5 → 54.7 %. |

**Decoy rejected.** Rank 51 runs at 84 °C, but its clocks are normal, no clocks-event reason is set, and
its compute is not an outlier. Warm is not slow (Section 13.9, step 6). The checker's
`hot_not_throttled` returns [51].

**Cost.** Steps 30–59 lose **334 GPU-s (17.3 %)**. The ideal step is 827 ms against an actual 1,004 ms.
Fixing rank 37 alone changes nothing while rank 12 is still slow. Rank 12's imbalance and the rail-2
leaf must both be fixed.

**Misleading metric.** `utilization.gpu` reads **99.7 % in every window**. NCCL kernels spin while ranks
wait, so the counter reports "busy" for idle waiting (Section 13.8). The second trap is the step-averaged
NIC rate (≈ 45 Gb/s). It looks idle and hides 360 Gb/s bursts during transfer, so "network
utilization high" is only true during the burst.

**Owners.** Data/Training Infra (sharding or sequence packing for rank 12), Fleet (cooling for the
node hosting rank 37), Network (`orion-be-leaf-r2`).
