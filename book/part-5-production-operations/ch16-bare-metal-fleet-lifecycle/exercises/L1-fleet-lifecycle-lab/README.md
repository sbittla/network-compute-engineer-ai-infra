# L1 · Fleet lifecycle automation lab (★★ · L1)

Type: hands-on-lab · Kind: lab · Points: 100

<!-- prompt:start -->
**L1 ★★ (L1) — Fleet lifecycle automation.** Complete [lab/README.md](../../lab/README.md) Tasks 1–5:
`check_compat`, `evaluate_node`, the lifecycle state machine with audit log, the upgrade-wave
planner, and the acceptance report.
*Evidence required:* `python lab/check.py` output showing 33/33 PASS; your `acceptance_report.md`
listing every non-PASS node with codes, the raw evidence values that triggered them, and the
remediation; the list of rejected lifecycle events with reason codes.
<!-- prompt:end -->

## What to submit

Put these files in `outputs/`:

- `check_output.txt` — the checker report, captured from the chapter folder with
  `cd lab && python check.py > ../exercises/L1-fleet-lifecycle-lab/outputs/check_output.txt`
- `acceptance_report.md` — from `cd lab && python report.py` (Task 5), edited so every non-PASS
  node lists its codes, the raw evidence values, and the remediation
- `rejected_events.md` — every rejected lifecycle event with its reason code
