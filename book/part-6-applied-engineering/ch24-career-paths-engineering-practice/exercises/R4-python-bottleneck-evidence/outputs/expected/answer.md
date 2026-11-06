# R4 — Is Python a hiring bottleneck? Model answer

**What the register shows** (`lab/data/job_register_2026-11.csv`, `[OBSERVED, 2026-11-06]`; `solve.py`
recounts it): Python appears in the required list of **25 of 50** roles (50.0 %), but the exact tag
"python" appears only **9** times. The other 16 are combined tags such as "python or go",
"python/bash/ansible" and "c/c++/python/go/rust". Kubernetes is in 13 required lists, Slurm 5, NCCL 3
(11 counting preferred). The synthetic register agrees in order (python in 27 of 31 clean postings,
`[ILLUSTRATIVE — synthetic data]`, Section 24.4).

**Why that is not yet a bottleneck claim.** A bottleneck means demand exceeds qualified supply, and the
register only measures one side, in one sample:
- **Sample limits.** One day (2026-11-06), a purposive sample of 50 roles at 11 employers (31 AI-cloud,
  12 frontier lab, 7 vendor) and **no hyperscaler**; 44 of 50 have a US location. The 2026-10-30 snapshot
  a week earlier shares 47 requisitions with it, so two snapshots are not two samples. You need a dated,
  deduplicated register over a defined, longer window and a sampling frame that includes the target
  employer group.
- **Segmentation.** Count by role family and level for *your* target role (for example the 7 SRE / ops
  roles), not across all 50.
- **Supply side.** The ratio of postings to qualified applicants, time-to-fill, or recruiter data. None of
  it is observable from postings.
- **Interview-loop evidence.** Whether candidates are actually rejected for Python (loop feedback, a
  hiring manager), as opposed to for fabric or GPU depth.
- **Vocabulary.** The combined tags signal a scripting *floor* ("Python or Go"), not a scarce specialism;
  map tags to a controlled vocabulary before counting (Table 24.9).

**Conclusion.** Frequency in postings is not scarcity. The defensible claim is "Python-level scripting is
a common entry requirement in this sample", labelled `[OBSERVED, 2026-11-06]` and stale after 2026-12-06.

**Common weak answers.** "Collect more postings" with no window, frame or segmentation; treating 25/50 as
a measure of importance; ignoring that the count depends on substring vs exact-tag matching.
