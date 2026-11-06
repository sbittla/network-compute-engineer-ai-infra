# Marking scheme: 10.H1 Link-health analyzer and commissioning report

Type hands-on-lab · kind lab · tier L1 · 100 points

**Evidence required:** `python check.py` output showing that all checks pass (the data-regeneration check may report SKIP); the generated `commissioning-report.md`; `diagnosis.md` explaining every non-healthy port (evidence, layer, root cause hypothesis, first safe action, missing hardware evidence) and every decoy you identified.

| Criterion | Points |
|---|---|
| Task 1–2: counter_delta, line rate, FEC margin and compute_deltas checks pass | 20 |
| Task 3: layer_classification, primary_findings, per_port_digest and severity_policy pass | 35 |
| Tasks 4–5: commissioning_report (FAIL, 57/64) and link_budget pass | 15 |
| Tasks 6–7: bom_and_spares and cabling_schedule pass | 20 |
| diagnosis.md: 1 point per correctly explained non-healthy port (9) + 1 for a decoy; −2 for cleaning Ethernet12/27, replacing Ethernet45's fiber, or touching an undrained link | 10 |
