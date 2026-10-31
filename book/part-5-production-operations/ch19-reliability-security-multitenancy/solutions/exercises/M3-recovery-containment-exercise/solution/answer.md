# M3 — Recovery and containment exercise (recovery test plan): reference solution

**Relies on:** Section 19.10 (Table 19.7a), Section 19.9 (isolation layers), Section 19.2 (blast-radius
control), Chapter 18 SLIs and burn rates. All thresholds `[ILLUSTRATIVE]`. Execution is on a
**dedicated lab partition only**, never on production or shared systems.

## 1. Hypothesis

"A failure confined to tenant A's footprint (repeated job crashes, a lost backend link, storage-quota
exhaustion) does not move tenant B's inference TTFT p95 or tenant C's training step-time ratio outside
SLO, and A's failures stay inside A's nodes, namespaces and paths."

## 2. Lab topology and steady state

Lab partition: 16 nodes on 2 rail-leaf groups, a dedicated Slurm controller and Lustre MDS instance
cloned from production configuration. A = 8-node training job (borealis-like); B = inference service on
2 nodes (cobalt-like, synthetic load at 60 % of peak); C = 4-node training job (acme-like) sharing spines
with A.

Steady-state SLIs over 30 min before each injection:

| SLI | Baseline method | Pass band |
|---|---|---|
| B TTFT p95 | median of 5-min windows | ≤ baseline + 10 % and within SLO |
| C step-time ratio (step / baseline step) | 30-min median | ≤ 1.03 |
| Scheduler latency (`sbatch` → start) | p95 | ≤ 2 × baseline |
| MDS op latency (C's checkpoint save) | p95 | ≤ 1.5 × baseline |
| Spine PFC pause rate on C's ports | median rate | ≤ 3 × baseline and ≤ 1,000/s |

## 3. Injections (three, each run alone, each reversible)

| # | Injection | Mechanism exercised | Method | Duration |
|---|---|---|---|---|
| I1 | A's job crashes and auto-restarts repeatedly | Scheduler and MDS restart-storm load; retry policy | `kill -9` A's ranks every 10 min | 60 min |
| I2 | One of A's backend ports disabled | Fault domain = one link; A hangs; does C see PFC or ECMP effects? | `shutdown` on A's rail-3 leaf port (lab leaf) | 30 min |
| I3 | A's storage quota filled | Storage isolation; MDS load; A's checkpoint failure handling | Write to A's fileset until quota | 30 min |
| I4 (optional) | A's tenant credentials used to list B's secrets | Identity and secrets isolation | Scripted read attempt with A's service account | 5 min |

## 4. Abort criteria and safety controls

- Abort immediately if any **non-target** SLI burn rate > 2, any alert fires on shared infrastructure
  (lab spine, MDS, controller), or the injection affects anything outside the lab partition.
- **Safety controls:** a written scope (named nodes, ports, filesets); change ticket and owner sign-off
  from Platform, Fabric, Storage and Security; a named exercise lead and an observer with stop authority;
  a kill switch per injection (restart A's ranks, `no shutdown` the port, delete the fill file); rollback
  rehearsed beforehand; a staffed weekday window; production change freeze honoured; no real tenant
  data on the lab partition.

## 5. Observations to record

B and C SLIs; spine utilization, PFC and ECN counters; scheduler RPC and queue latency; MDS latency; audit
logs (API, Slurm accounting, Vault, storage access) showing no cross-tenant access; timelines with
synchronized clocks.

## 6. Pass criteria

All non-target SLIs stay within their bands. A's failures are confined to A's nodes, namespaces and
paths. Audit shows zero cross-tenant reads. The retry policy stops I1 after 2 restarts in 6 h. I4 is
denied and logged.

## 7. Evidence

Timeline; dashboards (screenshots or exported series) per injection; audit-log excerpts; counter
snapshots before and after; the decision log with abort or continue per injection.

## 8. Tabletop run report

Walked through with Platform, Fabric, Storage, Security and the B/C service owners:

| Injection | Expected | "Discovered" in the walk-through | Gap | Follow-up (owner, due) |
|---|---|---|---|---|
| I1 restart storm | 2 auto-restarts, then a human gate; scheduler and MDS unaffected | Each restart re-reads A's full checkpoint at once (4 TB burst on a shared MDS); no per-tenant limit on restarts or on restore bandwidth | No per-tenant rate limit on job restarts or restore I/O | Platform: per-account restart limit; Storage: restore QoS per fileset (4 weeks) |
| I2 port down | A hangs then fails; C unaffected | A's 8.6 s retry budget expires; A's peers retransmit; nobody could say whether ECMP rehash moves C's flows onto a busier spine | Unknown cross-tenant effect of ECMP rehash; no per-tenant spine dashboards | Fabric: per-tenant spine utilization panel; run I2 first on hardware (2 weeks) |
| I3 quota full | A's checkpoint fails cleanly; MDS fine | A's trainer retries writes in a tight loop, which raises MDS load; the checkpoint is logged "complete" with missing shards | Trainer has no back-off; selection does not validate shard count | Training Infra: back-off and fail-fast; checkpoint validator (S2 in M1) (3 weeks) |
| I4 secret read | Denied, logged | Denied, but the denial is logged only in Vault, not forwarded to the SIEM | Audit gap for denied cross-tenant reads | Security: forward Vault audit to the SIEM with ≥ 365-day retention (1 week) |

Outcome: the plan was revised (I1 now includes restore-I/O monitoring; I3 adds a shard-count check) and
scheduled for execution on the lab partition after the follow-ups for I1 and I4 close.

## Marking notes

Deduct 3 points if the tabletop report is absent. Deduct for any injection outside a dedicated partition,
or for abort criteria that watch only the target tenant.
