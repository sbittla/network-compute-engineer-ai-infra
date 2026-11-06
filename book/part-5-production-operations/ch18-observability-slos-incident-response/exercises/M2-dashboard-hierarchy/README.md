# M2 · Dashboard hierarchy from fleet to workload (★★ · L1)

Type: outline-mandated · Kind: lab · Points: 15

<!-- prompt:start -->
**M2 ★★ L1 — Dashboard hierarchy.** Design the dashboard hierarchy from **fleet overview to node, GPU,
NIC, switch, and workload detail**. For each level: the one question it answers, 4–8 panels with
query and unit, and the drill-down key to the next level. Include a mock-up sketch (ASCII or image) of
the fleet level. *(Deliverable: dashboard mock-up; `dashboard_spec()` in the lab is the machine-checked
skeleton.)*
*Evidence required:* level table; mock-up; drill-down keys; justification of two panels you rejected.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Run the lab checker as shown below; this exercise is done when the named checks pass. [outputs/expected/](outputs/expected/README.md) shows those check lines from a finished lab, plus a worked answer and the marking scheme.

## What to submit

Put these files in `outputs/`:

- `dashboard_mockup.md` — level table, panels with query and unit, drill-down keys, fleet mock-up
  sketch, two rejected panels
- `dashboard_spec.json` — output of your `dashboard_spec()` (lab Task 6); check it with
  `cd lab && python check.py`
