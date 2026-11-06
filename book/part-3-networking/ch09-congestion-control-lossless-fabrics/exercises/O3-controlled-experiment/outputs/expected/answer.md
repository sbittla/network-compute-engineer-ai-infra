# O3 — Design a controlled congestion experiment (model answer)

Relies on manuscript Section 9.11 ("Designing a controlled experiment"), "Realism boundaries", lab
README Task 7 (configurations A/B) and §9 (L3 extension), and `lab/manifest.yaml` `record:` fields. The
lab's simulation numbers are `[SIMULATED]`; the experiment would produce `[MEASURED]` results.

**Chosen comparison:** ECN thresholds, A (as found) vs B (template).

| Element | Plan |
|---|---|
| **Hypothesis** (falsifiable) | On the lab leaf, Kmin 150 KB / Kmax 1,500 KB (B) reduces total TC 3 pause duration in a 12:1 incast by **≥ 5×** compared with Kmin 1,500 KB / Kmax 6,000 KB (A), and increases median incast completion time by **≤ 20 %** |
| **Configuration A** | Trust DSCP; DSCP 26 → TC 3, PFC priority 3 only; Xoff/Xon and headroom profile per real cable lengths; ECN on TC 3: Kmin 1,500 KB, Kmax 6,000 KB, Pmax 0.2, WRED drop off; PFC watchdog on; CNP DSCP 48 → TC 6 strict; NIC DCQCN at firmware defaults (recorded) |
| **Configuration B** | Identical except Kmin 150 KB, Kmax 1,500 KB |
| **Controlled variable** | Only the ECN profile (Kmin/Kmax) on the receiver leaf's TC 3 egress; both configs captured as full snapshots and diffed before the first run |
| **Workload** | 12 sender nodes running `ib_write_bw` to one destination NIC on the same rail; fixed message size (e.g. 4 MiB), fixed QP count, fixed duration or byte count; plus a **bystander probe** (`ib_write_lat`) from one sender NIC to an idle host |
| **Procedure** | Warm-up run discarded; **A/B interleaved** (ABABAB…) to cancel drift; **≥ 5 runs each**; counters snapshotted before and after each run; idle period between runs |
| **Metrics** | Per-client and aggregate bandwidth; incast completion time; bystander p50/p99/max latency; pause frames and **pause duration** tx/rx per port; ECN marks; `np_cnp_sent` / `rp_cnp_handled`; queue and PG watermarks; TC 3 discards; watchdog events |
| **Analysis** | Median and p95/p99 with min/max per config; ratio of medians for pause duration and completion; claim a difference only if the ranges do not overlap or a pre-registered test (e.g. Mann-Whitney U, α = 0.05) passes |
| **Manifest** | Every `lab/manifest.yaml` `record:` field: switch model/ASIC/NOS version, NIC model/firmware/driver, DCQCN parameters, buffer profile, cable lengths, MTU, perftest version and command lines, CPU pinning, date, evidence_class MEASURED |
| **Safety boundary** | Dedicated, isolated lab fabric only; no shared switches; a rollback snapshot of the switch config; stop on any TC 3 discard or watchdog trigger |

## What cannot be concluded from the lab's simulation (model-specific)

1. **Absolute magnitudes:** 960 µs, 862.8 µs paused and so on come from a single-queue fluid model,
   not an ASIC.
2. **Shared-buffer and per-PG behaviour:** dynamic thresholds, per-ingress-PG pausing and cell
   rounding are not modeled (the lab uses an aggregate view).
3. **Real DCQCN dynamics:** the model has fast recovery only, with no additive/hyper increase, no byte
   counter and no rate-reduction monitor, so B's ≈ 31 % completion penalty is likely overstated.
4. **NIC loss recovery:** config C assumes best-case selective repeat after 20 µs; go-back-N and
   tail-loss timeouts are absent.
5. **Multi-hop effects:** pause propagation, ECMP, HOL victims, storms, deadlock and watchdog
   behaviour.
6. **Generalization** beyond 12 synchronous, equal, line-rate senders.

## What the experiment would and would not establish

It **would** establish, as `[MEASURED]`, whether B reduces pause exposure and by how much, and its cost
in completion time and bystander latency, for *that* switch, NIC firmware, scale and workload. It
**would not** establish behaviour at ORION scale (multi-hop trees), with other NIC firmware or
workloads (all-to-all, storage), or long-term stability. Those need further, separately designed
experiments.
