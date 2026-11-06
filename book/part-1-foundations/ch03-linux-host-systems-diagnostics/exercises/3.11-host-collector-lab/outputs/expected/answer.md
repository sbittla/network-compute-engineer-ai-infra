# 3.11 — Host collector and fleet analyzer: reference solution

Reference implementations: `solutions/lab/host_collector.py` and `solutions/lab/host_analyzer.py`. Rubric:
`lab/README.md` Section 8. Methods: manuscript Sections 3.2–3.10. All snapshots are `[SIMULATED]`
(generator seed 3, instructor-only).

## Checker

`python check.py --impl solution` prints 21/21 PASS (committed as `solutions/lab/outputs/check_solution.txt`).
The recall and precision checks compare critical/warning findings with salted hashes of the 14 expected
(host, check, severity) keys, so learners learn *how many* they found, not which.

## Expected fleet result

| Host | Critical | Warning | Info | Verdict | Planted condition |
|---|---|---|---|---|---|
| orion-n01 | 0 | 0 | 1 | healthy (check gaps) | Reference; 2 historical corrected AER on NIC 4 (info only) |
| orion-n07 | 1 | 2 | 0 | DRAIN / repair | GPU 3 at Gen3 x8 under load; 37 corrected AER RxErr |
| orion-n12 | 1 | 6 | 0 | DRAIN / repair | nvme3n1 48.6 ms in md0; b ≈ 15; 98.9 % NUMA-remote; rail0/fe0 IRQs on CPU0 |
| orion-n19 | 3 | 1 | 0 | DRAIN / repair | NUMA node 1 short ≈ 252 GiB after RMA; rail3 MTU 1500; acpi-cpufreq powersave |
| orion-n23 | 1 | 2 | 0 | DRAIN / repair | rail5 at 200 Gb/s; 12 EDAC CE on MC2; Xid 63 on GPU 5 |
| orion-n28 | 0 | 0 | 12 | healthy (check gaps) | Non-root, idle, no sysstat: evidence gaps, sysfs fallback, idle downshift |

## Model triage memo (lab Part D.3)

| Host | Verdict | Evidence | Owner |
|---|---|---|---|
| orion-n07 | Drain at next checkpoint; reseat or replace the GPU 3 path | `LnkSta 8GT/s x8` under load; 37 AER RxErr | Fleet |
| orion-n12 | Drain; replace nvme3; fix IRQ profile; fix loader binding | 48.6 ms member latency; CPU0 100 % softirq; 98.9 % remote | Fleet, Platform, Training Infra |
| orion-n19 | Drain; DIMM investigation; full re-provision; MTU via config management | node1 774,107 MB; rail3 MTU 1500; 800 MHz | Fleet, Fabric |
| orion-n23 | Drain; rail5 optic/cable/port check; trend DIMM CE; GPU reset to apply row remap | 200 Gb/s; 12 CE on MC2; Xid 63 | Fabric, Fleet |
| orion-n28 | **Not cleared**: re-collect as root, with sysstat, under load | 3 evidence gaps | Fleet / on-call |
| orion-n01 | Healthy reference | — | — |

On a RoCE rail, `orion-n19`'s 1500 B netdev MTU also caps the RDMA active MTU at 1024 B
(docs/VERIFIED_FACTS.md), so the MTU finding is a performance fault, not cosmetic.

## Common mistakes

Counting every AER detail line (148 "events" on n07, and n01's noise becomes a warning); keeping the
since-boot `vmstat` row (n12's mean `b` drops to 12.2 and the parser check fails); using the first
`iostat` report (hides `nvme3n1`); stopping at `md0` instead of the member drive; warning on n28's idle
GPU downshift or `intel_pstate` powersave; treating `<access denied>` as "no PCIe devices"; computing IRQ
concentration per IRQ instead of per device; writing a deny-list guard (no A2 credit even if it passes).

The Exercise 3.8 report is graded from the 3.8 folder's answer; the inventory from 3.12.
