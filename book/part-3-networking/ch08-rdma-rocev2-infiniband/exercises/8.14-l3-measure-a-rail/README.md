# 8.14 — L3 extension: measure a rail (★★★, L3)

Type: Hands-on lab · kind: `written` · 10 points

## Prompt

<!-- prompt:start -->
**8.14 L3 extension: measure a rail** ★★★ · L3
On a dedicated lab fabric, collect real inventories from two nodes, run your validator, then run
`ib_write_bw -a` and `ib_write_lat -a` on at least two rails (five repetitions each, warm-up discarded,
NUMA-pinned). Compare the measured plateau and n½ with the Section 8.11 model for your link speed and
MTU.
*Evidence required:* raw captures; filled-in `manifest.yaml` with `evidence_class: MEASURED`; median
and min/max for plateau and p99/p99.9; model-versus-measured table with an explanation of any gap.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Run only on a dedicated lab fabric. Record the environment in `manifest.yaml` with `evidence_class: MEASURED`. Put every deliverable in `outputs/`:

- `outputs/raw/` (the unedited ib_write_bw / ib_write_lat captures and inventories)
- `outputs/manifest.yaml`
- `outputs/report.md` (median and min/max table, model-versus-measured table, gap explanation)

**Hardware run (course harness).** This exercise cannot be done on the course harness. `python
scripts/hw_labs.py run ch08` records the missing RDMA hardware, runs the readiness validator on the
host's real inventory and measures memory-registration cost (`lab/l2/results/`). That is useful
preparation, not a substitute for the two-host perftest runs. Run it from the repository root. The harness builds and runs a Docker image, so Docker must be running.