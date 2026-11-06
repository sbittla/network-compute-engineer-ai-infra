# Lab checks this exercise relies on

When your lab implementation is complete, `check.py` prints these lines (reference run):

| Check | Reference line |
|---|---|
| `p1.validate_planted_violations` | PASS p1.validate_planted_violations  4 violations, all planted ones found |
| `p1.validate_clean_and_cnp_rule` | PASS p1.validate_clean_and_cnp_rule  clean desired state passes; injected CNP/RoCE DSCP clash is caught |
| `p1.plan_diff_blocked_unreachable` | PASS p1.plan_diff_blocked_unreachable  24 actions on 22 targets; blocked and unreachable excluded |
| `p1.apply_default_is_dry_run` | PASS p1.apply_default_is_dry_run  apply_plan defaults to dry-run; zero writes |
| `p1.apply_cap_and_audit` | PASS p1.apply_cap_and_audit  blast-radius cap respected (8 targets); audit records complete |
| `p1.idempotent_converge_and_noop` | PASS p1.idempotent_converge_and_noop  3 capped batches converge; re-plan empty; re-apply is a recorded no-op |
| `p2.condition_semantics` | PASS p2.condition_semantics  relative_drop / relative_rise+floor / sum_gt behave correctly |
| `p2.wave_decisions` | PASS p2.wave_decisions  wave0 proceed; wave1 proceed (degraded node skipped, transient dip ignored); wave2 abort |
| `p2.bake_insufficient_hold` | PASS p2.bake_insufficient_hold  insufficient bake time -> hold |
| `p2.rollout_abort_and_rollback` | PASS p2.rollout_abort_and_rollback  abort at wave 2; roll back 8 changed nodes; waves 3-5 never start |
| `p3.review_coverage` | PASS p3.review_coverage  found 17/17 real gaps |
| `p3.review_false_positives` | PASS p3.review_false_positives  0 false positive(s) (limit 1) |
| `p3.review_evidence_quality` | PASS p3.review_evidence_quality  17 findings cite valid plan lines and concrete fixes |
