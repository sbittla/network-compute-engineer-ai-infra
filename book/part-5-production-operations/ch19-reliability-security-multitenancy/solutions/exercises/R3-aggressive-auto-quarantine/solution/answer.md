# R3 — Over-aggressive auto-quarantine: guidance and model answer

**Relies on:** Section 19.13 (the hang with no hardware fault); Section 19.6 (smallest *defensible*
domain); Section 19.7 (spares, retry policy); Table 19.8 (quarantine policy trade-off); lab
`data/spares.csv`.

## Two ways it reduces reliability (any two, with mechanism)

1. **It drains healthy nodes, so capacity and spares run out.** A rule like "quarantine the rank that
   timed out first" drains innocent nodes. The first reporter is arbitrary (rank 817 in the lab; rank 0
   on orion-n01 in Section 19.13). Every false drain removes a node that a fixed-size synchronous job
   needs. On ORION, with no spares, the 24-node job pended at 23 nodes until on-call borrowed inference
   node orion-n25. On ORION-XL, `spares.csv` shows only four of eight pool nodes `ready`, so a few false
   positives exhaust the pool. Restarts then wait, which raises RTO for *real* failures. The blast-radius
   variant, quarantining a leaf for one bad port, removes 31 healthy nodes' rail at once.
2. **It masks software faults with hardware churn.** In Section 19.13 the hang was a collective mismatch
   introduced by a logging change. Quarantining nodes "fixed" nothing: the hang recurred every 3,000
   steps on whatever node held rank 0. Meanwhile the real cause went undiagnosed. Each cycle cost a full
   restart, and repair queues filled with nodes that later pass diagnostics ("no fault found"). That
   delays repair of genuinely broken nodes and erodes trust in the health system.

A third acceptable answer: **remediation storms.** Automation that drains many nodes at once can
overload the scheduler, PXE/BMC and repair teams, turning a single fault into a fleet event (Chapter 20,
rate-limited remediation).

## The fix

Quarantine only with node-specific hardware evidence (Xid, fatal AER, link events, failed health
check). Rate-limit drains (at most *k* per hour). Escalate repeat offenders (two implications in 24 h)
rather than first reporters.
