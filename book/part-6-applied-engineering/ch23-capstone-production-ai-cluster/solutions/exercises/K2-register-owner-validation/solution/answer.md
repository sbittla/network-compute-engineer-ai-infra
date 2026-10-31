# K2 — Owner and validation fields in the assumptions register

**Source:** manuscript Section 23.2 (Table 23.3 and "Never let an assumption silently become a fact");
key K2.

An assumption is a number or statement the design relies on but has not proven *in this environment*.
The two fields make it accountable and falsifiable.

**`owner` — accountability.** The owner is the team that will validate the assumption and be paged
when production contradicts it. Failure mode when missing: nobody runs the validation, nobody notices
when reality diverges, and the value drifts from `[ILLUSTRATIVE]` in the register into the architecture
text without a label and finally into the benchmark table as if it were measured. Example on ORION:
A-07 (job MTBF 48 h, `[ILLUSTRATIVE]`) with no owner is never re-estimated from the first 90 days of
incident data, so the checkpoint interval stays tuned to a guess while infant-mortality failures make
the real M much shorter.

**`validation` — falsifiability.** The validation field states the procedure, the tier and the
acceptance criterion that would turn the assumption into a measurement (and what result would change
the design). Failure mode when missing or "TBD": reviewers cannot tell a belief from a measured value,
and nobody can say what evidence would prove it wrong. Example: A-04 (MFU 0.40) without "64-GPU slice
run, L3, accept if MFU ≥ 0.37" cannot be tested, yet moving MFU from 0.40 to 0.35 adds about 14 days to
a 96-day run (Section 23.2). The Kestrel bundle plants exactly this defect (A-07 with no validation,
linter rule COMP-002).

**Common wrong answer.** "For documentation" or "so we know who wrote it". The point is not record
keeping: the owner field creates a person who acts when the assumption fails, and the validation
field creates a test that can fail.
