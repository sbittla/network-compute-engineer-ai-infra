# M1 — Target role and skills map: reference answer and marking notes

Graded against the lab rubric items "own role-readiness matrix" (15) and "gap plan" (10). Method: Sections
24.2 and 24.9; scoring rules in `lab/data/competency_matrices.yaml`. All scores are `[MODELED]`.

**What a full-marks submission contains.**
1. `my_evidence.yaml` in the lab's evidence format: one item per artifact with type (course, lab_l1, lab_hw,
   capstone, case_study, production, self_assessment), competency id from the catalogue, date, artifact link
   and, for production, a verifier.
2. The lab report run on that file (not hand-computed), so evidence caps and flags are applied.
3. A matrix: target role plus the two adjacent roles of Figure 24.1 (for an AI Network target: GPU Compute /
   HPC and Network Hardware / Vendor), each at junior / mid / senior / staff, showing score and status.
4. The top three gaps ordered by weight × gap, each with an action, an artifact and a date.

**Worked illustration** (sample learner, AI Network target): scores 100.0 / 94.1 / 78.4 / 69.6 % for junior →
staff. Top gaps at senior: observability (2 × 2 = 4) → Capstone B by week 7; congestion (3 × 1 = 3) → the same
capstone's congestion study; host_topology (2 × 1 = 2) → an L2 GPU-host lab with manifest by week 10.

**Checks a marker applies.**
- Each level ≥ 3 must point at a capstone, hardware lab or published case study; level 4 needs a named
  verifier. Unsupported claims lose the artifact marks.
- Flags raised by the lab (STALE, NO_ARTIFACT, SIMULATION_CLAIMED_AS_MEASURED) must be resolved or explained,
  not ignored.
- An employer ladder may replace the lab matrices only if it is mapped onto the 0–4 scale with the mapping
  shown.

**Common mistakes.** Self-assessed levels typed into the matrix by hand; gaps listed without dates; adjacent
roles that share no competencies with the target.
