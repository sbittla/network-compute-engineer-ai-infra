# Chapter 20 — Answer Key (INSTRUCTOR ONLY)

Remove this folder before distributing to learners (`scripts/make_student_release.py`). All numbers
were computed twice: by hand, and with a short Python script. Values are `[ILLUSTRATIVE]`,
`[MODELED]` or `[SIMULATED]` as labelled.

---

## 20.1 Knowledge check

1. **Idempotent**: applying the operation once or many times yields the same end state.
   *Idempotent*: `ip link set dev eth1 mtu 9000`, or a gNMI `replace` of a leaf's QoS map.
   *Not idempotent*: NIC firmware flash plus reset, a reboot, appending a config line, or
   allocating an IP. Make it retry-safe by checking the **running** state first (flash only if
   running ≠ target; read back after reset), and by using an idempotency key per change and target
   so a retry returns the earlier result instead of acting again.
   *Marking*: 1 pt definition, 1 pt each example, 1 pt technique. Common mistake: "idempotent =
   safe". A reboot command can be "safe" yet is not idempotent.
2. **Level-triggered** acts on the current difference between desired and observed state.
   **Edge-triggered** acts on events ("node added"). After a day of downtime, an edge-triggered
   controller has missed every event in that day and never repairs drift. A level-triggered
   controller computes the current diff and converges. *Marking*: must mention missed events or
   drift.
3. **State**: the tool's record of the objects it manages and their last-known attributes.
   **Plan**: the computed diff between configuration and real/recorded state (create, update,
   replace, destroy). **Drift**: real state differing from recorded or declared state, typically
   from hand edits. Stop at **destroy** or **replace** (forced recreate) of a fabric object, because
   that is an outage. Common mistake: thinking `apply` re-reads the reviewed plan. Apply a saved
   plan file.
4. Syntax → schema → cross-object policy → pre-deployment analysis → post-deployment verification.
   Layer-3-only examples: leaf PFC on priority 4 while RoCE uses 3; `host_mtu + 22 > leaf
   port_mtu`; CNP DSCP 48 mapped to a PFC-enabled or non-strict class. Each value is valid in
   isolation; only the relationship is wrong.
5. Declarative; versioned and immutable; pulled automatically; continuously reconciled. A hand fix
   is reverted on the next reconcile. Break-glass: either an expedited, still-reviewed commit, or
   an explicit, time-limited, recorded pause of reconciliation for the specific target or field,
   with automatic expiry and a follow-up commit. Common mistake: "disable GitOps during
   incidents" fleet-wide.
6. **Proceed**: all changed nodes have full bake samples and no abort condition is breached (wave 0
   in the lab). **Hold**: evidence is insufficient, e.g. fewer than 12 post-change samples because
   the telemetry pipeline dropped data. **Abort**: any pre-declared condition is breached, e.g. a
   median busbw drop > 5 % on `orion-n25`. Hold ≠ abort: hold means "cannot tell", so no rollback
   yet, but no progress either.
7. Node-to-node baseline variation can exceed the regression to detect, so a fleet threshold either
   misses regressions on fast nodes or false-aborts on slow ones. A per-sample minimum turns any
   transient dip into an abort; in the lab, `orion-n09`'s single 7 % dip would abort wave 1. Median
   vs own-baseline median is robust to both.
8. Any five, each with its failure: dry-run default (accidental destructive run); blast-radius cap
   (too many targets or failure domains in one run); rate/concurrency limit (thundering herd on
   PXE/BMC/scheduler); kill switch (cannot stop a bad run); circuit breaker (ploughing on through
   failures); destructive-operation budget (automation draining too much capacity); two-person rule
   (single-person error); input sanity bounds (truncated input read as "remove everything").

---

## 20.2 Worked problem A — IPv6, VLAN-tagged variant

a. Leaf counts the full frame: frame = IP MTU + 14 (Ethernet) + 4 (802.1Q) + 4 (FCS) = IP MTU + 22.
   Max IP MTU = 9,100 − 22 = **9,078 B**.
b. IPv6 adds 20 B over IPv4, so the header budget = 64 + 20 = 84 B. Min IP MTU = 4,096 + 84 =
   **4,180 B**. (Exact fixed headers: IPv6 40 + UDP 8 + BTH 12 + ICRC 4 = 64 B, leaving 20 B for
   extended headers; RETH 16 + ImmDt 4 = 20 fits exactly.)
c. 9,000 + 22 = 9,022 ≤ 9,100 ✓ and 4,096 + 84 = 4,180 ≤ 9,000 ✓. **Valid.**
d. Overhead = 8 + 14 + 4 + 40 + 8 + 12 + 4 + 4 + 12 = **106 B** per packet.

   | RDMA MTU | Wire bytes | Efficiency | Packets/s at 50 × 10⁹ B/s `[MODELED]` |
   |---|---|---|---|
   | 1,024 | 1,130 | 1,024 / 1,130 = 90.6 % | 50e9 / 1,130 ≈ 44.2 M |
   | 4,096 | 4,202 | 4,096 / 4,202 = 97.5 % | 50e9 / 4,202 ≈ 11.9 M |

   The efficiency gain is 97.48 / 90.62 − 1 ≈ 7.6 %, larger than ORION's 5.9 % because the fixed
   overhead is bigger.
e. ```python
   def pol_mtu_fabric(node, leaves, pol):     # POL-MTU-FABRIC
       return node["host_mtu"] + pol["l2_overhead_bytes"] <= min(l["port_mtu"] for l in leaves)
   def pol_mtu_rdma(node, pol):               # POL-MTU-RDMA
       return (node["rdma_path_mtu"] in pol["allowed_rdma_path_mtu"]
               and node["rdma_path_mtu"] + pol["roce_header_budget_bytes"] <= node["host_mtu"])
   # policy data for this variant: l2_overhead_bytes = 22, roce_header_budget_bytes = 84
   ```
*Marking (10)*: a 2, b 2, c 1, d 3, e 2. Common mistakes: using 18 B L2 overhead (forgetting the
VLAN tag); keeping the IPv4 budget for IPv6; mixing Gb/s and GB/s (400 Gb/s = 50 GB/s).

---

## 20.3 Worked problem B — ORION-XL wave plan

a. Binomial approximation: P = 1 − 0.98⁸ = 1 − 0.851 = 0.149. Exact (hypergeometric, 10 affected
   of 512, 8 drawn without replacement): P = 1 − C(502, 8) / C(512, 8) ≈ **0.147**. Either is
   accepted with the method stated. For 90 %: 1 − 0.98ᵏ ≥ 0.9 →
   k ≥ ln 0.1 / ln 0.98 = −2.3026 / −0.0202 = 113.97 → **k = 114 nodes**. That is far too many for
   a canary.
b. Two affected nodes, each manifesting with 0.8: P = 1 − (1 − 0.8)² = 1 − 0.04 = **0.96**.
   Stratified selection beats size.
c. Example plan: **2, 6, 24, 96, 128, 128, 128** = 512 (7 waves). The maximum is 128 because there
   are 128 racks and at most one node per rack per wave. Duration = 7 × 75 = 525 min = **8.75 h**.
   Peak out of service = 128 / 512 = **25 %** of GPUs. GPU-hours = 512 × 8 × 1.25 h =
   **5,120 GPU-h** `[MODELED]`. Accept any plan of ≤ 8 waves that sums to 512, keeps each wave
   ≤ 128, and grows from a small canary (≤ 4 nodes).
d. After waves 0–2 of the example: 2 + 6 + 24 = 32 nodes; P = 1 − 0.98³² = 1 − 0.524 = **0.476**.
   Even after 32 nodes, a 2 % minority defect is a coin-flip under random selection, so wave size
   alone is not a detection strategy. Stratify using inventory attributes.
*Marking (10)*: a 3, b 2, c 3, d 2. Common mistake: computing k with log base confusion, or
assuming that independence holds when racks share a board revision.

---

## 20.4 Hands-on lab — answers and planted flaws

### Planted flaws (do not share with learners)

**Part 1 — desired state (`desired_state.json`)**

| Target | Override | Rule | Teaching point |
|---|---|---|---|
| `orion-n10` | `host_mtu: 9216` | POL-MTU-FABRIC (9,216 + 22 = 9,238 > 9,216) | RoCE is unaffected (packets bounded by the 4,096 path MTU); backend TCP/UDP packets of 9,216 B are dropped at the port and black-hole. The +22 B rule is a conservative portable policy; exact under full-frame switch MTU conventions |
| `orion-n22` | `nic_firmware: 28.44.0500` | POL-FW (not in approved list) | Configuration and lifecycle intersect: the Chapter 16 compatibility matrix gates intent |
| `orion-n25` | `ecn_enabled: "yes"` | SCHEMA (str vs bool) | Type coercion hides defects; schema failure short-circuits policy |
| `orion-be-leaf-r5` | `pfc_priorities: [4]` | POL-PFC | PFC on the wrong priority: RoCE becomes lossy on rail 5 while an empty class pauses; rail-specific busbw collapse |

**Part 1 — actual state (`actual_state.json`)**: rack-01 and rack-02 (`n01`–`n08`) already at RDMA MTU
4,096; rack-03 to rack-08 at 1,024 (RoCE MTU cap from an old host profile, manuscript §20.11); drift on
`orion-n06.host_mtu` = 1,500, with its `rdma_path_mtu` observed at 1,024 as a consequence (the largest IB
MTU under a 1,500-byte netdev MTU), `orion-n13.pfc_priorities` = [], and
`orion-be-leaf-r2.dscp_to_tc` missing `"48": 6`; `orion-n18` unreachable (`null`). Expected plan: 21 RDMA
MTU actions (20 in rack-03 to rack-08 + `n06`) + 3 other drift actions = **24 actions on 22 targets**.
On hardware, `n06`'s RDMA action is satisfied by the netdev fix and becomes a read-back check. Blocked: `orion-be-leaf-r5, orion-n10,
orion-n22, orion-n25`; unreachable: `orion-n18`. With cap 8: batches of 8, 8, 6; re-plan = 0.

**Part 2 — rollout (`rollout.json`)**

| Plant | Where | Trap | Correct behaviour |
|---|---|---|---|
| A — pre-existing fault | `orion-n13`, wave 1: precheck `health: degraded`, link flaps in baseline and post | Evaluating it trips AC5 → false abort of a good change | Skip and defer at precheck; send to repair (Chapter 16) |
| B — transient dip | `orion-n09`, wave 1: one post sample ≈ 7 % below baseline | `min`-based busbw check → false abort | Median-based AC1 → proceed |
| C — real regression | `orion-n25`, `orion-n29`, wave 2: busbw ≈ −10 %, CNP ≈ 5×, PFC ≈ 1.7–1.8× | PFC-only watching would proceed (1.8× < 3×, and ≈ 55/s < 150/s floor) | Abort on AC1 and AC2; rollback all 8 changed nodes |

Expected decisions: wave 0 proceed, wave 1 proceed (`n13` skipped), wave 2 abort. Rollback set:
`n01, n02, n05, n09, n17, n21, n25, n29`. Waves 3–5 not started. Deferred: `n13`.

**Part 3 — unsafe plan**: 17 real gaps (see `solutions/lab/findings.yaml`). G-OWNER, G-APPROVAL,
and G-COMMS are distractors: plan lines 3, 4, and 6 cover them. The pass thresholds are ≥ 13 of 17
found and ≤ 1 false positive.

### Answers to 20.4 a–c

a. `n10` MTU 9,216: RoCE is unaffected because its packets are sized by the 4,096-byte path MTU.
   Backend TCP/UDP (NCCL bootstrap/socket fallback, iperf/health checks, ssh over backend addresses;
   ORION storage uses the frontend NICs) sends 9,216-byte
   packets that exceed the leaf port and are dropped. With no ICMP reply they black-hole:
   connections open, but bulk transfers hang. Deduct a point if the answer claims RoCE breaks.
   `orion-be-leaf-r5` PFC [4]: RoCE on TC 3 is not protected on rail 5, so drops under incast lead to
   go-back-N retransmissions and a rail-5-only busbw collapse, while pauses on priority 4 are
   useless. `n22` firmware 28.44.0500: untested with the installed driver; risk of NIC init
   failures or subtle behaviour change outside the compatibility matrix. `n25` `"yes"`: depends on
   the consumer. It could be coerced to true, rejected at apply time mid-rollout, or disable ECN
   (DCQCN without ECN marks means no rate control, so PFC takes over).
b. (1) `n13` pre-existing flaps → AC5 would fire; prevented by precheck skip. (2) `n09` single-sample
   dip → a `min` statistic would fire; prevented by the median statistic.
c. `all_changed` is right because the regression mechanism (firmware behaviour under congestion) is
   load-dependent and could be latent on the wave 0–1 nodes under different traffic. Failing-wave
   only is defensible only if the regression is tied to an attribute unique to wave 2. Here
   `n25`/`n29` share nothing obvious with each other that `n21`/`n02` lack.

*Marking*: per lab README rubric (100 points).

---

## 20.5 Idempotent validator — reference outline

A good answer (Python or bash with `set -euo pipefail`):

```python
def observe(netdev, ibdev):
    link = json.loads(run(["ip", "-j", "link", "show", "dev", netdev]))[0]       # "mtu" field
    fw = parse_kv(run(["ethtool", "-i", netdev]))["firmware-version"]
    speed = int(Path(f"/sys/class/net/{netdev}/speed").read_text())               # Mb/s
    active_mtu = re.search(r"active_mtu:\s+(\d+)", run(["ibv_devinfo", "-d", ibdev])).group(1)
    return {"host_mtu": link["mtu"], "nic_firmware": fw, "speed_mbps": speed,
            "rdma_active_mtu": int(active_mtu)}

def main():
    desired = {"host_mtu": 9000, "rdma_active_mtu": 4096, "speed_mbps": 400000}
    drift = {k: (obs[k], v) for k, v in desired.items() if obs[k] != v}
    if obs["nic_firmware"] not in approved: drift["nic_firmware"] = (obs["nic_firmware"], approved)
    for k, (b, a) in drift.items(): audit(target, k, b, a, "drift")
    if args.apply and "host_mtu" in drift:          # only IP MTU is remediated
        if args.dry_run: audit(..., "dry-run")
        else: run(["ip", "link", "set", "dev", netdev, "mtu", "9000"]); audit(..., "changed")
    sys.exit(0 if not drift else 1)                 # 2 on exceptions / tool missing
```

Key marking points (10): machine-readable reads (2); exit codes 0/1/2 (1); validates without
mutating by default (2); apply touches only IP MTU and is a no-op second time (2); JSON audit lines
(2); handles a missing tool or device as "cannot determine", not "in sync" (1). Common mistakes:
treating `ibv_devinfo` failure as "in sync"; changing MTU on all NICs including the frontend; no
second-run evidence. Note that RDMA `active_mtu` follows the netdev MTU on many RoCE
implementations, so a learner who re-reads `active_mtu` after the MTU fix earns credit for
"read-back verification".

---

## 20.6 Canary rollout for the leaf QoS profile — model answer

1. **Prechecks**: all 8 leaves reachable via the management API and console (OOB); running config
   equals the git desired state (no drift); no active incidents; per-rail baselines captured over
   ≥ 60 min: ECN-marked/s, CNP/s, PFC pause tx/rx on TC 3, TC 3 drops (should be 0), and a
   2-node `all_reduce_perf` pair test per rail; Training Infra notified; rollback config rendered and
   staged.
2. **Wave plan**: one leaf per wave at first (at most two later), so a regression is confined to one rail of every node. Waves:
   `orion-be-leaf-r0` (canary) → `orion-be-leaf-r1` → `orion-be-leaf-r2` and `-r3` → `orion-be-leaf-r4` to `-r7`, one or two at a time. Bake ≥ 60 min
   under real training load per wave (CNP/PFC behaviour needs representative congestion,
   Table 20.8). Avoid the leaf with the most incast-heavy tenant first, but include it by wave 2.
3. **Success criteria** (per rail, vs that rail's own baseline median): pair-test busbw within 3 %;
   TC 3 drops = 0; CNP/s and ECN-marked/s within an expected band (tighter thresholds should
   *raise* ECN marks modestly, so state the expected direction); PFC pause rate not higher than
   baseline.
4. **Abort conditions** `[ILLUSTRATIVE]`: TC 3 drops > 0; PFC pause rate > 3× baseline and
   > 1,000/s; busbw drop > 5 %; NCCL timeouts or job-level step time > 5 % worse for jobs spanning
   the rail; any leaf control-plane alarm.
5. **Rollback**: full-config replace from the previous git commit via the device API, with
   commit-confirm where supported; scope = all changed leaves if the effect could be
   load-dependent; rehearsed on a lab leaf, time-bounded (< 5 min per leaf).
6. **Audit**: per leaf, before/after running config, diff, timestamps, actor, change ID, commit
   hash; per wave, baseline and bake metrics plus the decision with reasons; attached to the change
   record.

*Marking (20)*: 3 points per heading + 2 for rail-independence reasoning. Deduct for thresholds
without baseline method, missing "hold" for telemetry gaps, or changing multiple leaves in the
canary.

---

## 20.7 Unsafe plan review — reference

The reference `findings.yaml` (17 gaps) is in `solutions/lab/`. A good rewrite has **three**
changes in order: (1) NIC firmware 28.43.1014 via the Chapter 16 validated-bundle wave process,
(2) the leaf QoS profile one leaf per wave from git with dry-run diffs, (3) the RDMA MTU change via
the reconciler with node waves 2/3/4/8/8/7. Each has prechecks, a drain or reservation, bake,
abort conditions, rehearsed rollback, audit, OOB verification, a kill switch, and a staffed
weekday window. *Marking (20)*: checker results 10; rewrite quality 10. A common miss is
G-ORDERING (host/switch transitional mismatch) and G-OOB-ACCESS.

---

## 20.8 Troubleshooting case — model answer

a. Hypotheses:
   1. **Inventory truncation** (most likely): the log shows `items=16` with a `next=` page link, and
      16 targets fell to "default (lossy)". *Test*: query page 2; compare group size to
      yesterday's (32).
   2. Desired state changed: ruled out, because the commit `41aa9d3` is unchanged and yesterday
      planned 0.
   3. Real drift on 16 nodes: ruled out by direction. The plan moves nodes *away* from lossless,
      and the actual state matches yesterday's. *Test*: read 2–3 nodes directly.
b. **Root cause**: the reconciler's inventory client does not follow pagination. The API began
   returning 16 items per page (page size changed, or the group grew past a limit), so half the
   nodes were treated as members of no group and rendered with the lossy default.
c. Without controls: PFC removed and ECN disabled on 16 nodes (`n17`–`n32`) at 02:10. RoCE traffic
   from those nodes becomes lossy with no congestion control: drops, retransmissions, NCCL
   timeouts for every job spanning them. Stopping controls: input sanity bound (group membership
   changed by 50 % > 10 % → refuse); plan-size anomaly (48 ≫ 0–3 → hold for review);
   blast-radius cap (≤ 8 targets, ≤ 1 per rack); dry-run review (it was caught here); canary
   waves.
d. **Fix**: follow pagination; fail closed on partial reads. **Validate**: re-run the dry run →
   0 actions; unit test with a paginated fixture. **Guard**: a rule that a target's profile may not
   downgrade from lossless to lossy without an explicit, reviewed intent change, plus "group size
   delta > 10 % → halt".
*Marking (15)*: a 5, b 3, c 4, d 3.

---

## 20.9 Design challenge — marking guidance

Strong answers split fields by **ownership and risk**:

| Field class | Behaviour | Rationale |
|---|---|---|
| Lossless invariants (PFC priority, DSCP→TC map, CNP class, MTU) | Auto-revert, plus alert | A single wrong value breaks RoCE fabric-wide; no legitimate reason for hand edits |
| Tunables (ECN Kmin/Kmax, buffer thresholds) | Alert-only, with time-limited exemption | Legitimate incident tuning; must flow back to git |
| Interface admin state | Alert, plus lifecycle integration | Ports shut for repair are owned by the Chapter 16/10 workflows |

Break-glass: exemption object in git (target, fields, owner, reason, expiry ≤ 24 h) or an API
annotation the controller honours; auto-expiry; the audit record names the incident; a follow-up
PR is required to make the tuning permanent or let it revert. Fighting writers are prevented by
a single writer per field, the controller respecting exemptions, and an oscillation alert.
Scenarios: (1) incident tuning of ECN thresholds survives for its exemption period, then reverts
unless committed; (2) a technician mis-sets PFC during cabling work, and it is reverted within
5 min with an alert to Fabric. *Marking (15)*: table 5, break-glass 5, scenarios 5. Weak answers
pick one global policy.

---

## 20.10 Deliverable — marking guidance (30)

Automation sample (15): safety defaults present and documented (dry-run, cap, audit, kill-switch
hook) 8; tests or checker evidence 4; README clarity 3. Runbook (15): before/during/after 5;
signals and thresholds with sources 5; rollback, escalation, and audit bundle 5. Common weakness:
thresholds copied from the chapter without a baseline method.

---

## 20.11 Reflection — guidance

1. Accept the big bang only if the change is reversible in seconds (e.g. commit-confirm), was
   validated in an identical lab under representative load, the fleet is idle (no tail exposure),
   and the tail cost is explicitly accepted by the owner. Evidence: lab results, rehearsed revert
   time, idle-fleet confirmation.
2. Real telemetry has gaps and late samples (→ hold handling), counter resets and wraps (→ negative
   or huge rates), and correlated fleet-wide shifts from other causes (→ a baseline from a
   different load regime). Each could produce a false proceed or a false abort.
3. Example: "G-ROLLBACK — fix: add rollback" passes on the keyword but is rejected by a reviewer.
   It needs the saved config, a tested firmware downgrade, a time bound, and a scope.
4. Measured step time on W-TRAIN before and after (L3) with ≥ 5 repetitions, warm-up stated, one
   variable changed; NIC and switch counters showing packet-rate reduction; evidence that the
   network is on the critical path at all. With TP inside NVLink, DP and PP traffic may be partly
   overlapped with compute, so a 5.9 % ceiling rise may yield much less step-time gain.
