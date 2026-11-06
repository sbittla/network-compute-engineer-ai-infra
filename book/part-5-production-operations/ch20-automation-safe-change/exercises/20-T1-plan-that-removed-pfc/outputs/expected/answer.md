# 20-T1 — The plan that wanted to remove PFC: model answer

**Relies on:** manuscript Section 20.9 (Table 20.11, especially input sanity bounds and the "large plans are
suspicious" rule), Section 20.4.1 (inventory as source of truth) and the Chapter 9 RoCE QoS baseline.
Evidence is `[ILLUSTRATIVE]`.

## a. Ranked hypotheses and discriminating evidence

| Rank | Hypothesis | Evidence for / against | Discriminating test |
|---|---|---|---|
| 1 | **Inventory read truncated** (pagination not followed) | `items=16` with a `next=...page=2` link at 02:09:58; exactly 16 targets fell to "not in any lossless group → profile default (lossy)" | Fetch page 2 by hand: 16 more members (n17–n32)? Compare group size with yesterday's run (32) |
| 2 | Desired state changed | Commit `41aa9d3` unchanged since yesterday; yesterday planned 0 actions | `git log` on the repo; diff rendered profiles for n17 between yesterday and today |
| 3 | Real drift on 16 nodes | Direction is wrong: the plan moves nodes *away* from lossless, toward a profile they never had | Read 2–3 nodes directly (n17: PFC [3], ECN on, trust dscp?) |

Hypotheses 2 and 3 are ruled out by the evidence above; 1 is confirmed by page 2.

## b. Root cause

The reconciler's inventory client does not follow pagination. The API began returning 16 items per page (the
page size changed, or the group grew past a default limit), so the client saw only `orion-n01`–`n16` as members
of `roce-lossless`. The renderer then placed `orion-n17`–`n32` in "no lossless group" and rendered the lossy
default profile for them. The defect is a *partial read treated as a complete one*: the client should have
failed closed.

## c. Without safety controls

At 02:10 PFC would be removed (`[3] → []`), ECN disabled and trust mode switched to PCP on 16 nodes, half of
ORION's backend. RoCE traffic from those nodes becomes lossy with no congestion control and probably wrong
priority classification: drops under incast, go-back-N retransmissions, NCCL timeouts for every job spanning
them, and the night's training runs fall back to their last checkpoint.

Controls from Table 20.11 that stop it:

- **Input sanity bound**: group membership changed by 16 / 32 = 50 % > 10 % → refuse to plan.
- **Plan-size anomaly**: 48 actions against a normal 0–3 → hold for human review.
- **Blast-radius cap**: ≤ 8 nodes and ≤ 1 per rack per batch limits the damage to one batch.
- **Dry-run review**: this is how it was caught, because the nightly run posts a plan before applying.
- **Canary waves** and the destructive-operation guard would limit any residual exposure.

## d. Fix, validation, guard

- **Fix:** follow `next` links until exhausted; treat any failed page, missing count or inconsistent total as a
  failed read (fail closed, plan nothing, alert).
- **Validate:** unit test with a paginated fixture (2 pages of 16); rerun the dry run → **0 actions** against
  commit `41aa9d3`; confirm the run log shows 32 members.
- **New guard:** a policy rule that a target's profile may not *downgrade* from lossless to lossy without an
  explicit, reviewed intent change in git, plus "group size delta > 10 % between runs → halt".

## Marking (15 points)

a 5 · b 3 · c 4 · d 3. Full marks for (b) require tying the cause to the `items=16 ... next=` log line.
