# K8 — The three valid outcomes of a design review

**Source:** manuscript Section 23.6 ("Finding severities and outcomes"); key K8.

A design review is a meeting whose output is a decision, not a discussion. The three valid outcomes:

1. **Approved.** The design may proceed as written; no open blocker or major finding.
2. **Approved with conditions.** The design may proceed, but each condition (for example "rerun the
   leaf port arithmetic with both spares cabled" or "add a validation plan for A-07") has a named
   **owner** and a **date**, and the chair checks it is closed.
3. **Rework.** Blocker findings remain (for example a physically impossible leaf configuration such as
   34 + 32 = 66 ports on a 64-port switch); the design returns for another review.

**Why "we'll take it offline" is not an outcome.** It has no owner, no date and no decision, so the
review produces nothing anyone is accountable for: the contested finding is neither accepted nor
rejected, and it usually resurfaces in production.

**Common wrong answers.** "Accepted / rejected" only (misses conditional approval, the most common
real outcome); listing "deferred" or "needs discussion" as an outcome; conditions without owners or
dates, which are wishes rather than conditions.
