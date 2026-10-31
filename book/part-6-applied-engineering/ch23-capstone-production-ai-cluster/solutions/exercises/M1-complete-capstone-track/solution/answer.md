# M1 — Complete one capstone track (grading guide)

**Source:** manuscript Section 23.1 (Table 23.2 tracks, capstone workflow) and Sections 23.2–23.9;
`capstones/RUBRIC.md`; key G (M1).

There is no single model answer: the learner chooses one of capstones A–H. Grade as follows.

**1. Rubric scoring (`capstones/RUBRIC.md`).** Seven dimensions: R1 framing and assumptions (10), R2
architecture and technical correctness (20), R3 reproducibility (15), R4 measurement and analysis (20),
R5 reliability, security and operations (15), R6 troubleshooting and judgment (10), R7 communication (10).
- **Pass:** total ≥ 70/100 *and* R2 ≥ 10/20 *and* R4 ≥ 10/20.
- **Distinction:** ≥ 90/100 with reproducible evidence (every quantitative claim regenerates from
  committed code and inputs; every `[MEASURED]` claim has a manifest and repetitions).
- **Automatic cap:** presenting `[SIMULATED]`, `[MODELED]` or laptop-proxy numbers as physical
  measurements caps R4 at 40 % (8/20), which by itself fails the capstone because 8 < 10.

**2. Required artifacts.** Problem statement with the five elements (K1), assumptions register with owner
and validation for every entry (K2), architecture with ADRs and revisit triggers (Section 23.3),
consistency arithmetic (Table 23.5), failure-domain table and FMEA (Section 23.5), benchmark table with
labels, tiers and manifests (Section 23.7), failure-exercise report (Section 23.8), security
considerations, backlog (Section 23.9). A missing required section caps R7 at Developing.

**3. Lint gate.** Run the lab linter on the bundle: gate PASS, or each remaining finding waived in writing
with a reason a reviewer can accept (for example a NUM-001 on a number quoted from a cited standard).

**What a strong submission looks like.** An A-track (256-GPU training cluster) bundle that re-derives
ORION's invariants (256 GPUs, 8 × 4 × 8, 32 + 32 leaf ports, 512 links, 40.8 kW racks, 12.25 s checkpoint
floor), labels each number, and reports its one L3 measurement with a manifest.

**Common deductions.** `[MEASURED]` fabric numbers at L1; "Validation: TBD"; a gate FAIL with no waivers;
ADRs with no options considered.
