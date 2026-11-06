# D1 · Node acceptance specification and lifecycle runbook (★★★ · L1)

Type: deliverable · Kind: written · Points: 100

<!-- prompt:start -->
**D1 ★★★ (L1; L2/L3 optional) — Node acceptance automation specification and lifecycle runbook.**
Produce a document of 4–8 pages containing: (1) the acceptance specification (from M1) as a policy
file plus rationale; (2) the evaluator's input schema and reason-code catalogue (from the lab);
(3) the lifecycle state machine (from M3) with the audit-record schema; (4) the compatibility-matrix
process and the staged-upgrade procedure (from M2); (5) a runbook for "node fails acceptance" and
"node develops a hardware fault in production", with signals, thresholds, safe actions, evidence to
capture, and escalation paths; and (6) a realism section stating which parts were validated at L1
only.
*Evidence required:* the document; your lab `acceptance_report.md` as an appendix; `check.py` output;
for L2/L3, the filled `manifest.yaml` and raw command outputs.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 16 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Put these files in `outputs/`:

- `acceptance_spec_runbook.md` (or `.pdf`) — the 4–8 page document with sections (1)–(6)
- `acceptance_report.md` — your lab report (appendix)
- `check_output.txt` — from `cd lab && python check.py`
- L2/L3 only: your filled `manifest.yaml` and the raw command outputs
- L2 on one GPU: `python scripts/hw_labs.py run ch16 --device gpu` (CPU fallback: `--device cpu`) writes the raw outputs to `lab/l2/results/` Run it from the repository root. The harness builds and runs a Docker image, so Docker must be running.