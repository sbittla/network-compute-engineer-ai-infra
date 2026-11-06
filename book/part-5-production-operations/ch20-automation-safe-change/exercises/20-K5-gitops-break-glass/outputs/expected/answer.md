# 20-K5 — OpenGitOps and break-glass: worked answer

**Relies on:** manuscript Section 20.6.2 (OpenGitOps principles and their consequences) and the
fighting-writers scenario of Section 20.13.

## Model answer

The four OpenGitOps principles (CNCF OpenGitOps project):

1. The desired state is **declarative**.
2. It is **versioned and immutable**, held in a store such as git with full history.
3. It is **pulled automatically** by software agents.
4. It is **continuously reconciled**: agents observe actual state and converge it to desired state.

**Effect on a hand-applied break-glass fix:** the next reconcile pass sees the hand edit as drift and
reverts it, often within minutes. If the engineer re-applies it, human and controller fight; if a second
automated writer re-applies it, two controllers fight, which is exactly the periodic CNP-mapping incident
on `orion-be-leaf-r2` in Section 20.13.

**Handling break-glass under GitOps**, either:

- an **expedited, still-reviewed commit** (a second engineer approves quickly; the controller applies it
  like any other change), or
- an explicit, **time-limited, recorded exemption** that pauses reconciliation for the *specific target and
  field* only (for example `orion-be-leaf-r3` ECN thresholds on TC 3), with an owner, a reason that names the
  incident, automatic expiry, and a required follow-up commit that either makes the tuning permanent or lets
  it revert.

Either way the record shows who changed what, why, and when the exception ends.

## Marking notes (4 points)

2 points for the four principles (1 if one is missing); 1 point for "hand fix reverted on next reconcile";
1 point for a scoped, expiring, recorded break-glass mechanism.

**Common wrong answers.** "Disable GitOps during incidents" fleet-wide: every other drift then goes
unrepaired, and nobody remembers to re-enable it. Listing "push-based CI/CD" as a principle: GitOps is
pull-based.
