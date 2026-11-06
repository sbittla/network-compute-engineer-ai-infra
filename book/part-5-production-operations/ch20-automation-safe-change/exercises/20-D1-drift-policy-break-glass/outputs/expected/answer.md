# 20-D1 — Drift policy and break-glass for the ORION fabric: model answer

**Relies on:** manuscript Section 20.6.2 (GitOps consequences), Section 20.3.3 (single ownership of every
field), Section 20.13 (fighting writers on `orion-be-leaf-r2`) and Table 20.14 (drift-policy trade-off). Times
and limits are `[ILLUSTRATIVE]`.

The disagreement dissolves once fields are split by **ownership and risk** rather than choosing one global
policy: Fabric is right about invariants, Platform is right about tunables.

## Policy table

| Field class | Examples | Behaviour | Rationale |
|---|---|---|---|
| Lossless invariants | PFC priority (3), DSCP → TC map (26 → 3, 48 → 6), CNP class, trust mode, port MTU | **Auto-revert within 5 min, plus alert** to Fabric | One wrong value breaks RoCE fabric-wide or on a whole rail; there is no legitimate reason to hand-edit them |
| Tunables | ECN Kmin/Kmax and marking probability on TC 3, buffer/headroom thresholds | **Alert-only**, honour a time-limited exemption | Legitimate incident tuning; must flow back to git or expire |
| Interface admin state | port shut/no-shut | **Alert, integrate with lifecycle** | Ports shut for repair are owned by the Chapter 16 repair and Chapter 10 workflows |

## Break-glass procedure

1. **Who:** the on-call Fabric engineer during a declared incident; a second engineer acknowledges.
2. **How:** create an exemption object in git (or an API annotation the controller honours) naming target,
   fields, owner, incident ID, reason and **expiry ≤ 24 h**. The exemption is reviewed after the fact, not
   before, so it is fast.
3. **Recorded:** the controller logs the exemption, every write to the exempt fields, and the expiry.
4. **Expiry:** at expiry the controller reverts the field to git unless a follow-up PR has merged the tuning.
   The follow-up PR is a required incident action item.
5. Invariant fields **cannot** be exempted by on-call; changing them needs an expedited reviewed commit.

**Preventing fighting writers:** one writer per field (the GitOps controller), every other automation
(legacy cron templates) retired or made read-only; the controller respects exemptions instead of overwriting
them; an **oscillation alert** fires on > N writes to the same `target.key` within an hour by different actors.

## Scenario walk-throughs

1. **Incident tuning.** 03:10, a tenant's incast pushes PFC pauses on rail 3 high; on-call lowers Kmin on
   `orion-be-leaf-r3` TC 3 and files an exemption until 03:10 next day. The controller alerts on the drift but
   does not revert. Next morning the team either merges the tuning into git (it becomes desired state) or lets
   it expire and revert at 03:10. No writer fights; the audit shows who, why and for how long.
2. **Harmful hand edit.** During cabling work a technician mistakenly removes PFC on priority 3 on
   `orion-be-leaf-r6`. It is an invariant: the controller reverts it within 5 min and alerts Fabric. Exposure is
   bounded to one rail for ≤ 5 min instead of until someone notices a busbw collapse. If an engineer tries to
   exempt the field, the controller refuses because invariants are not exemptible.

A pure alert-only policy fails scenario 2; a pure auto-revert policy fails scenario 1 (on-call and controller
fight during an incident).

## Marking (15 points)

Table 5 · break-glass 5 · scenarios 5. Weak answers pick one global policy.
