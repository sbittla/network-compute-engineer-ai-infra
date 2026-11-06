# M2 — Conduct a design review (grading guide)

**Source:** manuscript Section 23.6 (roles and preparation, finding severities and outcomes,
Table 23.7 design-review checklist); key G (M2).

**Required evidence and what "good" looks like.**
1. **Reviewers.** At least two people who did not write the design, ideally covering different layers
   (compute and network, or network and operations). A chair who owns the outcome.
2. **Pre-read.** The bundle (problem statement, register, ADRs, failure domains, benchmark table) and the
   lab linter's report, sent before the meeting so reviewers arrive with written findings.
3. **Findings with severities**, written *before* the meeting, each pointing at an artifact: e.g.
   "Blocker — topology.yaml: 34 + 32 = 66 > 64 leaf ports"; "Major — A-07 has no validation plan";
   "Minor — ADR-005 revisit trigger is a date, not an event". Coverage must include explicit assumptions,
   trade-offs (ADRs), failure domains and operational constraints, using the 40-item Table 23.7 checklist.
4. **Outcome.** One of approved, approved with conditions, or rework (K8). "We'll take it offline" earns
   nothing.
5. **Conditions** each with an owner and a date, e.g. "Fabric: recompute leaf arithmetic with spares
   cabled, by 2026-11-14".
6. **Updated bundle**, shown as a diff or changelog that closes each condition, plus a rerun lint report.

**Deduct** for a review that is a presentation with no recorded findings; reviewers who are co-authors;
findings without severities; conditions without owners or dates; no evidence the bundle changed.
