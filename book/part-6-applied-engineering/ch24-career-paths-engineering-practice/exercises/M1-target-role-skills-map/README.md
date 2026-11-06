# M1 — Target role and skills map (★★, L1)

Outline-mandated · difficulty ★★ · tier L1 · kind `written` · [exercise index](../README.md)

<!-- prompt:start -->
**M1 ★★ L1 — Target role and skills map** *(course outline, Chapter 24 exercise 1)*. Select a target
role and map your current skills to its competency requirements using the lab's matrices (or your
employer's ladder, mapped onto the 0–4 scale). Every demonstrated level must cite an artifact.
*Evidence required:* the lab report run on your evidence file; a matrix with role, two adjacent roles,
four seniority columns; top three gaps with dated actions.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the worked answer and marking scheme in the chapter's `solutions/exercises/M1-target-role-skills-map/` (instructor material in the full repository; removed from student releases).

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/readiness_report.md`
- `outputs/skills_map.md`
- `outputs/my_evidence.yaml`

Run:

```bash
python ../../lab/starter/career_lab.py --data <my_data/> --role <role> --seniority <level> --out outputs/readiness_report.md
```

`<my_data/>` is a copy of `lab/data/` whose `learner_evidence.yaml` is your own evidence (keep the original so `check.py` still passes); also copy it to `outputs/my_evidence.yaml`.
