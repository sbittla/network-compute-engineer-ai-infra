# WP1 — Readiness for a second role (★★, L1)

Worked problem · difficulty ★★ · tier L1 · kind `computed` · [exercise index](../README.md)

<!-- prompt:start -->
**WP1 ★★ L1 — Readiness for a second role.** Using the sample learner's demonstrated levels (from the
lab's `demonstrated_levels` output: observability 1, reliability/security 2, automation 3, scheduling 1, storage/checkpointing 1,
Linux host 2, communication 3) and the AI Infrastructure SRE / Operations matrix in
`lab/data/competency_matrices.yaml` at **mid** level:
(a) compute the readiness score with every term shown; (b) give the status and why; (c) produce the gap
plan ordered by priority; (d) compute the new score and status if Capstone F raises observability to 3.
*Evidence required:* a table of w, d, t and w·min(d,t)/t; the score to one decimal; ordered gap list with
priorities; the recomputed score and status.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 24 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Run:

```bash
python ../../lab/starter/career_lab.py --role sre_ops --seniority mid --out outputs/readiness_sre_mid.md   # optional cross-check after the lab
```
