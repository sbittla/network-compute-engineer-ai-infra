# T1 — The interview troubleshooting round, version 2: worked solution

All evidence is `[ILLUSTRATIVE]` (prompt); the magnitude check is `[MODELED]`. Method: the diagnostic loop
of Section 24.12 and the hypothesis ranking of Chapter 22 (Section 22.3).

**Hypotheses, ranked by information value, cost and risk**

| # | Hypothesis | Info value | Cost | Risk | Test |
|---|---|---|---|---|---|
| H1 | Software thermal slowdown of GPU 5 on `orion-n22`, from an airflow deficit after the 02:10 `rack-06` fan-tray work | High: directly explains late ranks | Low (read-only) | None | Temperatures and clocks of every GPU in `rack-06`; BMC fan sensors (Redfish Thermal resource or `ipmitool sdr type Fan`) |
| H2 | Fabric congestion on rail 5 (ECN marks 3×), or ECN as a *consequence* of the straggler | Medium | Low | None | PFC pause and drop counters on rail-5 ports; is the ECN rise concentrated on ports facing `orion-n22`'s peers and timed with its late arrivals? |
| H3 | Software change (driver, NCCL, framework) | Low: only one node is affected | Low | None | Package versions on `orion-n22` vs peers; change log |
| H4 | Failing GPU independent of cooling (e.g. cold-plate or heatsink contact) | Medium | Medium (drain + DCGM diagnostics) | Low once drained | `dcgmi diag` after drain; compare after airflow is restored |

**Discriminating tests and both outcomes.** (1) Rack-wide thermal read: if other `rack-06` GPUs are also
warm or the replaced tray's fan sensors read low or absent, H1 with an airflow cause is strongly supported;
if only GPU 5 is hot with normal fans, H4 (GPU-local) rises. (2) Rail-5 counters: flat PFC and drops plus
an ECN rise that tracks `orion-n22`'s late arrivals supports "ECN is a consequence" (a late rank releases
pipeline sends in bursts that mark ECN); ECN rising on ports unrelated to `orion-n22` means H2 needs its
own investigation.

**Magnitude check.** Compute is ≈ 13.90 / 17.90 = 77.7 % of the step (Chapter 22, Table 22.2), so
≈ 13.5 s of 17.4 s. Scaling with SM clock against peers at the ≈ 1,830 MHz sustained clock: 13.5 × 1,830 / 1,585 =
13.5 × 1.155 = 15.6 s, **+2.1 s → 19.5 s (+12 %)**, matching the symptom. Treat +2.1 s as an upper bound:
memory-bound kernels slow less than the clock ratio. Note the baseline choice: comparing against the
1,980 MHz maximum boost instead of the peers' sustained clock would predict ≈ 3.4 s and overstate the effect;
always say which peer clock you compared against.

**Root cause.** *Proven:* GPU 5 is in SW thermal slowdown (event reason active, 89 °C, 1,585 / 1,830 = 87 %
of peer clock); its TP group waits for it and its ranks gate the pipeline. *Inferred (correlation):* the
fan-tray replacement caused the airflow deficit; Facilities must confirm.

**Safe change.** With the job owner, drain `orion-n22` in the scheduler (stops new placement; it does not
move the running job), then restart from the latest checkpoint at DP = 7 / 224 GPUs with a batch/LR
adjustment, or wait for repair (ORION has no spares). Facilities inspects the fan tray under their
procedure. Do not raise power limits, override clocks, reset the GPU under a running job or touch fabric QoS.

**Validation.** Burn-in with GPU 5 within the peer range (64–70 °C) and no active clock-event reasons; node
acceptance (Chapter 16) before return; job p50 back to ≈ 17.4 s over ≥ 100 steps in ≥ 5 comparison
windows; rail-5 ECN rate back to baseline, which confirms H2 was a consequence.

**Common wrong answers.** Treating the ECN rise as the root cause; declaring the fan tray proven; proposing
fan or power-limit changes in production without Facilities. "Clocks Event Reasons" is the current label
("Clocks Throttle Reasons" on older drivers); the DCGM field is `DCGM_FI_DEV_CLOCKS_EVENT_REASONS`
`[VENDOR-SPEC, 2026-10]`.
