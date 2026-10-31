# L1 — Design-review linter (reference solution notes)

**Source:** lab/README.md Tasks 1–8; manuscript Sections 23.4–23.7 and 23.11; key Section C.
Reference implementation: `solutions/lab/design_lint.py`; `python lab/check.py --impl solution` →
**13/13 PASS** (outputs in `solutions/lab/outputs/check_solution.txt`). Evidence class: the linter
runtime on a laptop is `[MEASURED]`; everything it checks is `[MODELED]` arithmetic over the bundle.

## Expected linter results

- Kestrel bundle: **20 findings (6 blocker, 14 major), gate FAIL**. Blockers: COMP-001 (design.md has no
  "Failure exercise" section), GPU-001 (34 nodes, spares 0, total 256), GPU-002 (TP × PP × DP = 8 × 4 × 16
  = 512 ≠ 256), PORT-001 (34 + 32 = 66 > 64), POWER-001 × 2 (rack-07 and rack-08: 5 × 10.2 = 51 kW > 45 kW).
- Majors: PORT-002 ("1:1" claimed vs 34:32 = 1.06:1), CABLE-001 (512 listed vs 8 × 66 = 528), EVID-001
  (B-03 empty label), EVID-002 (B-05 "ESTIMATED", not a valid label), EVID-003 (B-02 MEASURED without a
  manifest), EVID-004 (B-04 8-node busbw MEASURED at L1), NUM-001 × 2 (design.md lines 18 and 29), XREF-001
  (A-12 cited but absent), COMP-002 × 2 (A-07 no validation; SLO-03 no window), FD-001 (FD-06 storage
  metadata with redundancy none and no mitigation), FD-002 (scheduler class not analyzed), SLO-001
  (SLO-04 target "low").
- Reference ORION bundle: **0 findings, gate PASS**. Any finding there is a false positive.

## Traps that must *not* be flagged

PORT-004 (34 downlinks equal the BOM's 34 nodes, so consistent); FD-07 rack power with redundancy `none`
but a real mitigation (DP replicas spread across racks); design.md L28 numbers attributed by benchmark
ID; L19's labelled 10.2 kW `[VENDOR-SPEC, 2026-10]`; B-06 (laptop linter runtime, legitimately MEASURED).

## Triage memo (Task 8)

- **Design defects** (change what is built): GPU-001/002, PORT-001/002, CABLE-001, POWER-001 × 2,
  FD-001, FD-002.
- **Documentation/evidence defects** (change what is claimed): COMP-001, COMP-002 × 2, EVID-001..004,
  NUM-001 × 2, XREF-001, SLO-001.
- **Linter false positives:** none.
- **Raise first:** POWER-001 or PORT-001 — physical impossibilities that change rack count or switch
  SKU, hence cost and schedule. Both share a root cause with GPU-001 (two spares added late without
  rerunning the arithmetic), so present them as one finding with three symptoms. Minimal fixes are the
  W1 repairs: declare spares 2, DP = 8, 34 down + 28 up (1.21:1), 496 cables, 9 racks or a validated
  9.0 kW cap.

**Common mistakes.** Flagging PORT-004 on Kestrel (confusing "inconsistent with intent" with
"inconsistent with the BOM"); sizing POWER-001 with sustained power; reporting a rack over budget twice;
deleting findings instead of explaining them in the memo.
