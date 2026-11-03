# 20-K8 — Fleet-automation safety controls: worked answer

**Relies on:** manuscript Section 20.9 and Table 20.11 (ORION settings `[ILLUSTRATIVE]`).

## Model answer

Any five of the eight controls, each paired with the failure it prevents:

| Control | Specific failure prevented | ORION setting `[ILLUSTRATIVE]` |
|---|---|---|
| Dry run by default | Running a destructive command by accident; reviewing code but never its effect | `--dry-run` is the default; apply needs an explicit flag and a change ID |
| Blast-radius cap | One run touching too many targets or failure domains at once | ≤ 1 node per rack, ≤ 8 nodes and ≤ 1 rail leaf per batch; > 25 % of fleet needs second approval |
| Rate / concurrency limit | Thundering herd: reboots overwhelming PXE/DHCP/image servers, the BMC network or the scheduler | ≤ 4 concurrent node operations; ≤ 8 reboots per 10 min |
| Kill switch | Being unable to stop a run that is going wrong | Flag checked before every target and every wave |
| Circuit breaker | Automation ploughing on through a growing failure rate | Stop if > 2 targets or > 10 % of attempted targets fail |
| Destructive-operation budget | Repair automation draining a large share of capacity | ≤ 2 nodes per day auto-drained per rack, then page a human |
| Two-person rule | One person's mistake reaching production | Second approver for destroy/replace or fabric-wide plans |
| Input sanity bounds | A truncated or empty inventory read as "remove everything" | Refuse if target count differs from inventory by > 10 %; refuse empty desired state |
| Automation identity | A stolen or over-privileged controller credential reaching every target | One scoped, short-lived credential per controller and target class; signed, pinned releases; separate break-glass |

The mechanism matters more than the name. For example, the input sanity bound exists because a reconciler
that receives half its inventory concludes, correctly by its own logic, that half the fleet should be
reconfigured to defaults, and then acts at full speed; Exercise 20-T1 is that failure. A plan-size anomaly
check (a reconciler that normally plans 0–3 actions suddenly plans 48) is the same defence seen from the
output side.

## Marking notes (5 points)

1 point per control correctly paired with its failure (maximum 5). No credit for a control name without its
failure mode.

**Common wrong answers.** Listing generic practices (monitoring, documentation) as controls. Describing a
kill switch as "Ctrl-C on the operator's laptop": it must be checked by the automation before every target.
