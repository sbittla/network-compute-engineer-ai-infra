# K7 — TTD, TTM, TTR and the onset bias

Definitions (Section 18.11, Table 18.8a), all measured from **onset** = first minute of sustained SLI
degradation in workload metrics:
- **TTD** (time to detect) = detection (first alert or human report) − onset.
- **TTM** (time to mitigate) = mitigation (user impact stopped, e.g. rollback complete and SLI
  recovering) − onset.
- **TTR** (time to resolve) = resolution (all-clear criteria met) − onset.

INC-2291 `[SIMULATED]`: onset 02:10 (step-time series), detection 02:58 (a researcher's chat message),
mitigation 04:08:12, resolution 04:30 → TTD 48.0 min, TTM 118.2 min, TTR 140.0 min; detection was
41 % of the time to mitigation.

**Why onset must come from telemetry.** Human reports lag the real onset by the time users take to
notice and decide to complain (48 minutes in INC-2291). Taking the first report as onset would set
TTD ≈ 0, understate impact (GPU-hours lost before anyone noticed), and hide exactly the alerting gap
the postmortem must fix, the missing training-throughput alert.

Report all three numbers: an aggregate MTTR hides whether the team is slow to notice or slow to fix.
