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

## What to submit

Put every deliverable in [`outputs/`](outputs/):

- `outputs/check.txt`: the `check.py` output showing 21/21 PASS
- `outputs/fleet_report.md`: the generated fleet report
- `outputs/n12_report.md`: the Exercise 3.8 troubleshooting report
- `outputs/triage_memo.md`: the fleet triage memo (lab Part D.3)

Command to run (from this folder):

```bash
cd ../../lab && python check.py | tee ../exercises/3.11-host-collector-lab/outputs/check.txt
cd ../../lab && python starter/host_analyzer.py data/snapshots/*.json --baseline data/orion_hx8_baseline.yaml --out ../exercises/3.11-host-collector-lab/outputs/fleet_report.md
```

Label every number (`[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`) and show formula, substitution and result with units. Quote raw snapshot lines where you rely on them.
