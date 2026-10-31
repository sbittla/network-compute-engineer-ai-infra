# 14.18 — Deliverable: I/O benchmark plan and checkpoint/recovery design (★★★, L1 (L2/L3 optional))

Type: deliverable · Kind: lab

## Prompt

<!-- prompt:start -->
**14.18 Deliverable: I/O benchmark plan and checkpoint/recovery design** ★★★ · L1 (L2/L3 optional)
**(outline)**
Produce a document (≤ 6 pages) containing: (1) an I/O benchmark plan for ORION covering local
NVMe, PFS bandwidth, PFS metadata rate, and read-under-write interference — each with tool, exact
parameters, warm-up, ≥ 5 repetitions, percentiles reported, and the manifest fields recorded; (2) a
checkpoint/recovery design for W-TRAIN: strategy, interval, staging buffers, commit protocol,
validation ladder, retention, and archive; (3) an RPO/RTO analysis with time-to-resume broken into
components and lost accelerator-hours per day; (4) a restore test procedure; (5) an explicit
statement of which values are modeled and which are measured. *Evidence required:* the document,
the planner output it cites, and the validator run on the lab store.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/deliverable.md (≤ 6 pages)`
- `outputs/planner_output.txt`
- `outputs/validator_run.txt`

Run:

```bash
python lab/check.py
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
