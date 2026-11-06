# D1 — A 12-week plan from "near" to "ready" (★★★, L1)

Design challenge · difficulty ★★★ · tier L1 · kind `written` · [exercise index](../README.md)

<!-- prompt:start -->
**D1 ★★★ L1 — A 12-week plan from "near" to "ready".** Pick a role and level at which your own
readiness (from the lab) is "near" or "not_ready". Design a 12-week plan to reach "ready" with no more
than 10 hours per week. Choose between depth (one capstone to level 3 plus a hardware lab) and breadth
(two capstones at L1), and between L1-only and paying for L2 GPU time. Defend the choice with the
readiness arithmetic and the evidence caps.
*Evidence required:* current matrix; plan with dated artifacts and hours; projected score and status
after each artifact; one paragraph on what you are *not* doing and why.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the worked answer and marking scheme in the chapter's `solutions/exercises/D1-twelve-week-plan/` (instructor material in the full repository; removed from student releases).

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/plan.md`
- `outputs/readiness_report.md`

Run:

```bash
python ../../lab/starter/career_lab.py --data <my_data/> --role <role> --seniority <level> --out outputs/readiness_report.md
```

`<my_data/>` is a copy of `lab/data/` with your own `learner_evidence.yaml`. Use your own evidence file; the sample learner's numbers below are only for checking your arithmetic.

**Sample learner (unchanged `lab/data/learner_evidence.yaml`), for arithmetic checks only.** With your
completed `career_lab.py`, run it with `--data ../../lab/data --role ai_network --seniority senior`. The
manuscript's Table 24.5 gives the expected result for AI Network Engineer (senior): weighted coverage
**13.333 / 17 = 78.4 %, status "near"**, largest gap observability (1 → 3, gap 2). If the sample data
does not give 78.4 % and "near", fix your arithmetic before you plan from your own evidence.
