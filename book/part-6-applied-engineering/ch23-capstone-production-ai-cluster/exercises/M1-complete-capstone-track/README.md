# M1 — Complete one capstone track (★★★, L1)

Outline-mandated · difficulty ★★★ · tier L1 · kind `written` · [exercise index](../README.md)

<!-- prompt:start -->
**M1 ★★★ L1 (L2/L3 optional) — Complete one capstone track.** Complete one of the capstone tracks
in [`capstones/`](../../../../../capstones/) (A–H) following its brief and
[`capstones/RUBRIC.md`](../../../../../capstones/RUBRIC.md).
*Evidence required:* every required artifact listed in the chosen brief; a design bundle that lints
with gate PASS (or with each remaining finding explicitly waived with a reason); evidence labels on
every number.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the worked answer and marking scheme in the chapter's `solutions/exercises/M1-complete-capstone-track/` (instructor material in the full repository; removed from student releases).

## Mapping your capstone to a lint bundle

No capstone produces the linter's bundle directly, so you assemble one. The full mapping is in
[Lab 23 §7, "Mapping your capstone to a lint bundle"](../../lab/README.md#mapping-your-capstone-to-a-lint-bundle).
In short:

- Finish Lab 23 first. The command below runs *your* `lab/starter/design_lint.py`, and the
  unmodified starter raises `NotImplementedError`.
- Create `outputs/bundle/` with all seven files: `design.md`, `assumptions.yaml`, `bom.yaml`,
  `topology.yaml`, `failure_domains.yaml`, `slos.yaml` and `benchmarks.md`, plus `manifests/` for any
  `MEASURED` row. A missing file is a COMP-001 blocker. The linter has no waiver or not-applicable
  switch.
- Translate your track's artifacts: the design document → `design.md` (the seven exact `##` headings);
  the assumptions register → `assumptions.yaml`; the results table → `benchmarks.md`; the failure
  analysis → `failure_domains.yaml` (all eight classes); SLOs or acceptance targets → `slos.yaml`.
- Tracks B–H have no BOM or topology of their own. Describe the cluster the track runs on: copy
  `lab/data/bundle_orion_reference/bom.yaml` and `topology.yaml` for unchanged ORION-256, or write
  consistent counts for the cluster your brief declares. Empty files lint clean but prove nothing.
- Record any finding you judge not applicable in a `## Waivers` table (rule, location, reason,
  covering artifact) after the generated report in `outputs/lint_report.md`.

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/capstone/ (the chosen track's deliverables)`
- `outputs/lint_report.md`

Run:

```bash
python ../../lab/starter/design_lint.py outputs/bundle --out outputs/lint_report.md
```
