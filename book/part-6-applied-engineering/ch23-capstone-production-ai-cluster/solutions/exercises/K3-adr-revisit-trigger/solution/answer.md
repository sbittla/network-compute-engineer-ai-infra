# K3 — The ADR revisit trigger

**Source:** manuscript Section 23.3 (Table 23.4 and Example ADR-005); key K3.

**Purpose.** An ADR records why a choice was made, what else was considered and the consequences. The
revisit trigger is the line that makes the decision *self-monitoring*: it names an observable
condition under which the decision must be reopened, so the team learns it was wrong from telemetry or
an event rather than from a retrospective. Without it, an accepted ADR becomes folklore that nobody
re-examines when its context changes.

**Context of the ORION decision.** TP exchanges activations every layer and is latency-sensitive.
NVLink provides 450 GB/s per direction per GPU versus 50 GB/s line rate for one 400 Gb/s NIC
`[VENDOR-SPEC, 2026-10]`, a ratio of 450 / 50 = 9×. Keeping TP = 8 inside one HX8 node keeps per-layer
collectives on the fast path.

**Revisit trigger (observable):** reopen ADR-005 if any of the following is detected:
1. A planned model's per-GPU memory footprint at TP = 8, PP = 4 exceeds 80 GB (computed by the
   workload model in the design CI) — the layout no longer fits HBM.
2. The weekly placement audit (`scontrol show job` node lists compared with TP group membership) finds
   any TP group spanning more than one node — the assumption that placement keeps TP local is broken
   (this is exactly the Chapter 22 incident).
3. A new platform's NVLink-to-NIC bandwidth ratio falls below 4× — the speed argument weakens.

Each item is a metric with a threshold or a detectable event; none is "when we feel the model has
outgrown it".

**Common wrong answers.** "Revisit annually" (a calendar date, not evidence); "if performance is
bad" (not measurable without a metric and threshold); "when the team thinks TP should change" (an
opinion).
