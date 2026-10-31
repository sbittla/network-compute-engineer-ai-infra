# 20.6 — Canary rollout for the leaf QoS profile: model design

**Relies on:** manuscript Sections 20.7.1–20.7.4 (Tables 20.8 and 20.9), 20.8 (Table 20.10 rollback for
device config), 20.9 (blast-radius cap: ≤ 1 rail leaf per batch) and 20.10 (audit). ORION QoS: DSCP 26 →
TC 3 lossless with PFC; CNP DSCP 48 → TC 6 strict priority. All thresholds are `[ILLUSTRATIVE]` or derived
from the stated baselines.

**Rail independence.** Each rail leaf `orion-be-leaf-rN` carries rail N of all 32 nodes. Changing one leaf
therefore touches one of eight rails on *every* node: NCCL keeps running on the other seven, and the changed
rail can be compared against seven unchanged ones under the same job. Changing two leaves at once halves that
control group and doubles the exposure of every collective; the canary is one leaf.

## 1. Prechecks

- Per leaf: reachable via the management API **and** the console (out of band); running config equals the git
  desired state (no drift); no active alarms; rollback config (previous commit) rendered and staged.
- Fabric-wide: no open incidents; no other change in flight on hosts or leaves; Training Infra notified.
- Baselines per rail over ≥ 60 min of representative training load: TC 3 ECN-marked/s, CNP/s (TC 6), PFC pause
  tx/rx on TC 3, TC 3 drops (expected 0), and a 2-node `all_reduce_perf` pair test per rail (6 runs).

## 2. Wave plan

Wave 0: `orion-be-leaf-r0` (canary). Wave 1: `-r1`. Wave 2: `-r2` (include the rail of the most incast-heavy
tenant by here, not first). Waves 3–5: `-r3`, then `-r4`/`-r5`, then `-r6`/`-r7` (never more than two). Bake
**≥ 60 min under real training load** per wave: Table 20.8 puts CNP/PFC behaviour changes at minutes to an hour
and requires representative congestion; a pair test alone does not create incast. Total ≈ 6 × 75 min ≈ 7.5 h.

## 3. Success criteria (per rail, against that rail's own baseline median)

Pair-test busbw within 3 %; TC 3 drops = 0; ECN marks expected to **rise** modestly (tighter Kmin/Kmax), CNP/s
within the predicted band (state it, e.g. ≤ 2× baseline); PFC pause rate on TC 3 not above baseline; job step time
within 2 % for jobs spanning the rail.

## 4. Abort conditions (declared before wave 0)

| ID | Statistic | Abort if |
|---|---|---|
| Q1 | TC 3 drops, sum over bake | > 0 |
| Q2 | PFC pauses on TC 3, median per minute | > 3 × baseline **and** > 1,000/s |
| Q3 | pair-test busbw, median vs baseline median | drop > 5 % |
| Q4 | step time of jobs spanning the rail, median | > 5 % worse; or any NCCL timeout |
| Q5 | leaf control-plane alarm or link flap | any |

Missing telemetry for > 1 sample → **hold**, not proceed.

## 5. Rollback

Full-config replace from the previous git commit via the device API, with commit-confirm where the platform
offers it (auto-revert if not confirmed). Scope: all changed leaves, because a buffer/ECN effect is
load-dependent and may be latent. Rehearsed on a lab leaf with the same automation; time bound < 5 min per leaf,
verified by read-back of the DSCP map, PFC and ECN settings.

## 6. Audit evidence

Per leaf: before and after running config, diff, timestamps (UTC), actor, change ID, git commit, approver,
read-back result. Per wave: baseline and bake metrics, decision with reasons. Stored in the append-only audit
store and attached to the change record.

## Marking (20 points)

3 per heading + 2 for rail-independence reasoning. Deduct for thresholds without a baseline method, a missing
hold for telemetry gaps, or more than one leaf in the canary.
