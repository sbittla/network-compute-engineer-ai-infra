# Exercise 2.4 — ORION capacity, BOM, power, and SPOF lab

**Difficulty:** ★★ · **Tier:** L1 · **Type:** hands-on-lab · **Kind:** lab · **Points:** 100

## Prompt

<!-- prompt:start -->
Complete the [Chapter 2 lab](../../lab/README.md): implement `validate_inputs`, `compute_bom`,
`compute_power_cooling`, `compute_capacity`, `failed_set`, and `find_spofs` in
`lab/starter/capacity_model.py` until `python check.py` reports 14/14.

**Evidence required:** `check.py` output; the written deliverable from lab/README.md Section 7 (BOM
table, capacity spreadsheet, findings list with one consequence sentence per finding, failure-domain
diagram with mitigations and accept/fix decisions). For an L2/L3 extension, add a filled-in copy of
`lab/manifest.yaml` and raw measurement files.
<!-- prompt:end -->

## What to submit

Put every deliverable in [`outputs/`](outputs/):

- `outputs/check.txt`: the `check.py` output (14/14; the data-regeneration check prints SKIP in the student edition)
- `outputs/bom.md`: BOM table with optics and twin-port assumptions
- `outputs/capacity.csv`: capacity spreadsheet export
- `outputs/findings.md`: one consequence sentence per input-sheet finding
- `outputs/failure_domains.md`: failure-domain diagram with mitigations and fix/accept decisions

Command to run (from this folder):

```bash
cd ../../lab && python check.py | tee ../exercises/2.4-orion-capacity-lab/outputs/check.txt
```

Label every number you produce (`[MODELED]`, `[ILLUSTRATIVE]`, `[MEASURED]` and so on) and show formula, substitution and result with units.

**Hardware run (course harness).** For the L2 extension on the course harness, run `python
scripts/hw_labs.py run ch02 --device gpu` from the repository root (the CPU fallback runs automatically
without a GPU) and add its `lab/l2/results/<gpu-model|cpu-fallback>/environment.json` and `report.md` to
`outputs/`.
