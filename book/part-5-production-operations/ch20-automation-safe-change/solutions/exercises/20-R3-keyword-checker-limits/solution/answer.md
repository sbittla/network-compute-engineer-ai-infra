# 20-R3 — A finding that passes the checker but fails review: model answer

**Relies on:** lab README Section 6 (the Part 3 checks are a progress meter), `lab/data/unsafe_change_plan.md`
line 24, and manuscript Section 20.8 (Table 20.10, the three rollback rules).

## Model answer (≤ 150 words)

**Weak finding (passes):** `G-ROLLBACK, line 24: "fix: add a rollback plan with a saved config"`. It cites a valid
line and names a control, so `p3.review_evidence_quality` accepts it.

**Why a senior reviewer rejects it:** it does not say *how* each of the three changes is reversed, how long it
takes, or what scope. "Reimage the affected nodes" (line 24) does not roll back firmware at all.

**Improved:** "Per change: leaf QoS by full-config replace from the previous git commit with commit-confirm,
< 5 min per leaf; RDMA MTU by reconciling to the previous desired state, then re-creating QPs; firmware by
flashing 28.42.1000, checked against anti-rollback policy and rehearsed in the lab with the same automation
(timed). Before-state captured per target at apply time. Scope: all changed targets."

## Marking (5 points)

Weak finding identified 2 · improved finding with mechanism, numbers, scope and time bound 3.
