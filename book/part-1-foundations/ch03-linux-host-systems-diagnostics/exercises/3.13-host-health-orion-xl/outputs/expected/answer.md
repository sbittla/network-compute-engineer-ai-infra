# 3.13 — Host health at ORION-XL scale: model design note

Method: manuscript Sections 3.9–3.10 (first ten minutes, safe collector), the analyzer severity policy
(lab Part C) and `docs/REFERENCE_CLUSTER.md` (ORION-XL: 512 nodes, job MTBF ≈ 3 h). Snapshot sizes are
measured from the supplied `[SIMULATED]` files by `solve.py`; volumes `[MODELED]`.

## Decision table

| Decision | Choice | Rationale |
|---|---|---|
| (a) Continuous | node exporter + DCGM exporter every 10–30 s: utilization, temperature, clocks and clock-event reasons, ECC, Xid, PCIe replay, NIC counters (Chapter 18) | Cheap, unprivileged, catches trends |
| (a) On demand | the collector, triggered by straggler detection, any critical exporter alert, node acceptance, and RMA return | Rich evidence only where it pays |
| (b) Privilege | Unprivileged on live nodes (sysfs, journal group membership); root only on drained nodes or via an audited privileged agent, every run logged with who/why | Small blast radius, auditable |
| (c) Auto-drain at next checkpoint | `PCIE_WIDTH_DEGRADED`, `PCIE_AER_UNCORRECTED`, `MEM_ECC_UNCORRECTED`, critical Xids, `LINK_SPEED_DEGRADED`, `INVENTORY_MISMATCH` | Unambiguous and costly to leave in |
| (c) Page a human | Rate/context findings: CE trends, `IRQ_CONCENTRATION`, `NUMA_REMOTE_MEMORY`, `IO_SATURATION`, `CPUFREQ_*` | False positives likely; fix is often software |
| (d) Retention | 90 days hot (incident review), 1 year compressed, acceptance and RMA snapshots kept for the node's life | Matches incident and warranty timelines |
| (e) Baseline change | Git, pull request reviewed by Fleet and SRE, shadow mode then canary | Thresholds are code |

**(c) in GPU-hours.** A false drain costs one node: 8 GPUs × time to inspect and return (≈ 8 GPU-h for a
1 h check). A missed straggler in a 4,096-GPU synchronous job costs a share of the *whole job*: the
Section 3.11 Gen3 x8 fault costs ≈ 5.5 % of every GPU, ≈ 225 GPU-h per hour at ORION-XL scale. Auto-drain
is right when the finding is unambiguous; for ambiguous findings a human is cheaper than a false drain
storm. The drain itself waits for the next checkpoint, and with MTBF ≈ 3 h the next restart is rarely far.

**(d) Snapshot volume.** The six supplied snapshots are 75.9–155.8 KB (median ≈ 141 KB). One full sweep is
512 × 141 KB ≈ **72 MB**; daily sweeps are ≈ **26 GB per year** before compression. JSON text compresses
roughly 5–10×, so ≈ 3–5 GB per year compressed: storage is not the constraint, retention policy is.

**(e) Baseline change control.** `orion_hx8_baseline.yaml` lives in Git. A change goes through a pull
request with Fleet and SRE review. The new thresholds first run in shadow mode against a sample of nodes
(findings logged, not acted on), then canary, then fleet-wide, as in Chapter 20. Each analyzer report
records the baseline commit it used.

## Rejected alternatives

1. **Run the full collector as root continuously on every node.** Rejected: a large blast radius for a
   privileged agent, audit noise, and collection jitter on training nodes, for evidence that is only
   needed after a trigger.
2. **Alert on every corrected error.** Rejected: alert fatigue. Corrected AER and EDAC CE events occur on
   healthy hardware (`orion-n01`), so rate-based rules per BDF and per DIMM are required.
3. Also acceptable: **auto-drain on every warning**, rejected because at 512 nodes a 1 % false-positive
   rate drains ≈ 5 nodes per sweep.
