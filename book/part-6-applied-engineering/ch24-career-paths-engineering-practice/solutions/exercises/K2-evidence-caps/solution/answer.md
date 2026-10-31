# K2 — Evidence caps: model answer

Source: Table 24.2 (the 0–4 proficiency scale) and Figure 24.5 (the evidence ladder) in Sections 24.2 and
24.9; the same caps are `type_caps` in `lab/data/competency_matrices.yaml` (course 1, lab_l1 2, capstone /
lab_hw / case_study 3, production 4).

**Course → at most level 1 ("Aware").** Completing a course shows exposure to vocabulary and mechanisms. It
contains no artifact of the learner *doing* anything, so the only observable behaviour it supports is
"can explain the concept at whiteboard level".

**Level-1 lab → at most level 2 ("Working").** An L1 lab shows the learner can reproduce a defined
analysis on supplied data, following the lab specification. The problem, the data and the acceptance
criteria were given, so it proves guided execution, not independent judgment. A simulation presented as a
measurement is capped at 1, because it is an integrity failure, not a style issue.

**What level 3 ("Independent") needs.** Evidence that the learner *framed* the problem and defended the
choices without a spec: an open-ended capstone with ADRs, a hardware-backed L2/L3 lab with an environment
manifest and repetitions, or a published case study with a discriminating test. The behaviour that
changes is "designs, diagnoses and defends decisions without guidance".

**What level 4 ("Expert") needs.** Production ownership, verified by someone else (a named verifier or
reference). Only production exposes a person to real failure, scale and accountability, and only a
verifier stops the most common inflation (an unverified production claim is capped at 3; evidence older
than three years or undated loses one level).

**Common mistakes.** Equating level with years of experience; treating a certification as level 3; saying
"a lab proves level 3 if it was hard".
