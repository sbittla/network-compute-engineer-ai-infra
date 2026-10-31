# O1 — Investigate an end-to-end workload regression (solution)

All values `[SIMULATED]` (lab bundle, seed 2214); `solve.py` recomputes every number from `lab/data/`.

**(a)** Tasks 1–7 as in the L1 key: 8,990 clean rows; 7 TP-split jobs; time-aware factors; +23.2 % mean,
+13.1 % median; effects and attribution; storage cross-check consistent.

**(b) Corroboration table.** Each cause gets one *direct* measurement of its mechanism, independent of the
regression (Section 22.4.5).

| Cause | Direct evidence | Values |
|---|---|---|
| TP split (CHG-7790) | `node_metrics.csv`, after period, TP-split vs not: backend tx per node; SM active | 6.06 → 37.93 GB/s; 0.57 → 0.40 |
| Capacity tier (CHG-7795) | Step log data wait, TP-packed after-period jobs, capacity minus hot; `node_metrics.csv` CPU iowait hot → capacity; per-job p99 vs p50 | +1.46 s per step; 1.52 % → 6.03 %; p99 18.8 → 35.0 s while p50 18.17 → 18.24 s |
| R570 driver / GDR (CHG-7781) | `node_metrics.csv` host bounce copy on orion-n17..n32, before → after; `nccl_init_sample.log` channel lines `via NET/IB/0` (no `/GDRDMA`) on orion-n17 vs `/GDRDMA` on orion-n09; empty `lsmod \| grep nvidia_peermem`; inventory `peermem_module_loaded = no` | 0.40 → 9.50 GB/s (other nodes 0.39 → 0.42). Valid only because DMA-BUF is unavailable on these nodes `[VENDOR-SPEC, 2026-10]` |
| ECC alert on orion-n13 (ruled out) | `node_metrics.csv` SBE per job-node and GPU temperature on orion-n13 | SBE 0.7 → 152; temperature 67.4 → 68.1 °C; model effect −0.05 ± 0.09 s |

The storage evidence has the latency-tail fingerprint of Section 22.10.4: p99 doubles while p50 barely
moves, which a bandwidth problem would not produce.

**(c) Interaction model.** Refit with both `tp_split × storage_new` and `tp_split × driver_new`:

| Term | Coefficient ± SE (s/step) | |coef| / SE |
|---|---|---|
| `tp_x_storage` | −1.30 ± 0.15 | ≈ 8.6 |
| `tp_x_driver` | +0.03 ± 0.13 | ≈ 0.3 |

Other terms barely move (after 0.34, TP 8.94, driver 0.89, storage 1.40). **Judgment:** keep the
TP × storage interaction, which the dataloader-slack model predicts and the data confirm at ≈ 8.6 SE,
and drop TP × driver as negligible; the model with the single `tp_x_storage` term is defensible, while the
additive-only model is not, because it distorts storage (1.03 s), the common shift (0.73 s) and the alert
(−0.43 ± 0.14 s, spuriously "significant").

**Common wrong answers.** Citing the regression coefficient as its own corroboration; using the current
inventory for the bounce-copy split; keeping every interaction "to be safe" without SE reasoning.
