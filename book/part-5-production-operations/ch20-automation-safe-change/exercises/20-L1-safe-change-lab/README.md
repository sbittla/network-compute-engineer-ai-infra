# 20-L1 — Lab 20: safe-change automation (★★, L1)

Type: Hands-on lab · Kind: `lab` · Points: 100

## Prompt

<!-- prompt:start -->
Complete [Lab 20](../../lab/README.md), Parts 1–3. Then answer:

a. For each planted invalid desired value found by `validate_desired`, describe the RoCE failure it
   would have caused on ORION if applied.
b. Explain the two wave-1 situations that would make a naive controller abort, and the design
   choice in your controller that prevents each.
c. Justify `rollback_scope: all_changed` for this rollout, or argue for failing-wave-only.

**Evidence required:** `python check.py` output with all checks PASS; the decision log from
`run_rollout`; written answers a–c (≤ 1 page). L2/L3: a filled-in copy of `lab/manifest.yaml` with
the extension fields.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md). Values are ORION `[ILLUSTRATIVE]` unless stated.
- **Checking your work:** Run the lab checker as shown below; this exercise is done when the named checks pass.

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/check_output.txt` (python check.py, all PASS)
- `outputs/decision_log.md` (wave -> decision -> reasons)
- `outputs/answers.md` (a-c, <= 1 page)
- `outputs/manifest.yaml` (L2/L3 only)

Run:

```bash
cd ../../lab && python check.py
```

**Hardware run (course harness).** L2 on the course harness: `python scripts/hw_labs.py run ch20` feeds
measured GPU (or CPU) samples through your `evaluate_wave` / `run_rollout`, covering a no-op change, an
injected regression and a short bake. Its `lab/l2/results/<gpu-model|cpu-fallback>/environment.json` can
back the manifest fields. Run it from the repository root. The harness builds and runs a Docker image, so Docker must be running.