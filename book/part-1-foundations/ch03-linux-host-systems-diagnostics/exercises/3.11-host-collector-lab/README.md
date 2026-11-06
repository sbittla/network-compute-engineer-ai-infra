# Exercise 3.11 — Host collector and fleet analyzer (Lab 3, Progressive Lab 1)

**Difficulty:** ★★★ · **Tier:** L1 · **Type:** hands-on-lab · **Kind:** lab · **Points:** 100

## Prompt

<!-- prompt:start -->
Complete [`lab/README.md`](../../lab/README.md) Parts A–D: a **Python script that collects selected host
metrics and produces a timestamped report** (`host_collector.py`), and an analyzer that triages six ORION
snapshots against the HX8 baseline.
*Evidence required:* `python check.py` output showing 21/21 PASS; the generated `fleet_report.md`; the
written report for Exercise 3.8; and the fleet triage memo (lab Part D.3).
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Run the lab checker as shown below; this exercise is done when the named checks pass. [outputs/expected/](outputs/expected/README.md) shows those check lines from a finished lab, plus a worked answer and the marking scheme.

## What to submit

Put every deliverable in [`outputs/`](outputs/):

- `outputs/check.txt`: the `check.py` output showing 21/21 PASS
- `outputs/fleet_report.md`: the generated fleet report
- The Exercise 3.8 troubleshooting report: submit it once, as [`../3.8-cpu-low-throughput-poor/outputs/report.md`](../3.8-cpu-low-throughput-poor/outputs/report.md); do not copy it here
- `outputs/triage_memo.md`: the fleet triage memo (lab Part D.3)

Command to run (from this folder):

```bash
cd ../../lab && python check.py | tee ../exercises/3.11-host-collector-lab/outputs/check.txt
python starter/host_analyzer.py data/snapshots/*.json --baseline data/orion_hx8_baseline.yaml --out ../exercises/3.11-host-collector-lab/outputs/fleet_report.md
```

Label every number (`[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`) and show formula, substitution and result with units. Quote raw snapshot lines where you rely on them.
