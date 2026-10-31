# 20.1.2 — Level- vs edge-triggered controllers: worked answer

**Relies on:** manuscript Section 20.3.2, and the reconciliation loop of Figure 20.1 (Section 20.3.1).

## Model answer

A **level-triggered** controller acts on the *current difference* between desired and observed
state. Each pass observes the target, diffs it against the desired state, and plans only what differs.
An **edge-triggered** controller acts on *events*: "a node was added, configure it", "a commit landed,
push it".

The difference matters after downtime. Suppose the ORION host-config controller is down for a day.
During that day a node is reimaged (its backend NIC comes back at IP MTU 1,500, as `orion-n06` did in the
Section 20.11 example), and an engineer hand-edits a leaf's DSCP map. An edge-triggered controller missed
both events. When it restarts it has nothing to react to, so the drift stays forever, or until another
event happens to touch the same object. A level-triggered controller restarted after a day, or a week,
simply computes the current diff, finds `orion-n06.host_mtu` 1,500 → 9,000 and the leaf map difference,
and converges. On an in-sync fleet its next pass is an empty plan.

That is why the chapter's advice is to build reconcilers, not event handlers, wherever the target state
can be declared. Events are still useful as *hints* that trigger an early pass, but correctness must
not depend on receiving them.

## Marking notes (3 points)

1 point for each definition; 1 point for the downtime consequence (missed events, drift never repaired
vs current diff converges). The answer must mention missed events or drift to earn the third point.

**Common wrong answers.** Confusing the terms with electronics vocabulary without applying them to
controllers. Claiming that an edge-triggered controller "replays" missed events: only if a durable
event log exists and is replayed, and even then hand edits that produced no event are invisible to it.
