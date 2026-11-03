# T1 — The afternoon slowdown in rack-04

**1. Decode.** `0x24 = 0x20 | 0x04` → SW Thermal Slowdown + SW Power Cap (GPUs 4 and 5 at 86–87 °C,
1,590–1,650 MHz). `0x4` alone (GPU 6 at 15:10 at 1,830 MHz; all GPUs at 03:10 at 1,815–1,845 MHz) is
normal power capping under load: a power-capped GPU sits at its sustained clock, below the
1,980 MHz max boost. Judge throttling against the peers' sustained clock (≈ 1,830 MHz), not max
boost: GPUs 4 and 5 are 1 − 1,650/1,830 ≈ 10 % and 1 − 1,590/1,830 ≈ 13 % below their peers.

**2–3. Ranked hypotheses and discriminating tests**

| Rank | Hypothesis | For / against | Discriminating test |
|---|---|---|---|
| H1 | Rack-level airflow/cooling problem in rack-04 | All four rack-04 nodes show inlet 31–32 °C at 15:00 vs 24–25 °C in rack-03/05; FAC-2210 removed a cold-aisle containment panel two weeks ago; inlet rises with the facility's daily load cycle | Log inlet for all rack-04 nodes and the cold-aisle sensor over 24 h; inspect the containment; compare with rack-03/05 at the same time |
| H2 | Node-level fan or heatsink fault on orion-n14 | Would not raise the *inlet* of four nodes, nor recover at night | Fan RPM and per-GPU temperature rise above inlet vs rack peers at equal inlet temperature |
| H3 | Workload change (hotter kernels in the afternoon) | Same job on other racks is fine; 03:10 shows the same job at 71–76 °C | Run the same job on rack-03 nodes in the afternoon |

**4. Root cause, safe change, validation.** The missing containment panel lets hot exhaust
recirculate into rack-04's inlets. In the afternoon the facility runs warmer, inlet reaches
31–32 °C, the GPUs' thermal margin disappears, they hit the software thermal limit (`0x20`), and the
synchronous 128-GPU job runs at the pace of its slowest GPU, so p99 step time is 9 % above p50 only
in the afternoon and only on rack-04 placements. This explains both *time of day* (facility load)
and *rack locality* (one containment breach).
*Safe change:* Facilities reinstalls the panel under a facilities change ticket (non-disruptive to
IT load).
*Validation (pass thresholds):* for 3 consecutive days, rack-04 inlet ≤ 27 °C at 15:00 (the
ASHRAE-recommended upper bound for most IT classes; verify against your facility's design), no
`0x20`/`0x40` reasons on rack-04 GPUs, and the job's step-time p99/p50 back within normal spread
(≤ 3 %) `[ILLUSTRATIVE thresholds]`.

**5. Lifecycle decision.** Do *not* fault-drain, send to repair, or RMA: the hardware passed
acceptance and is healthy. Until validated, steer large synchronous jobs away from rack-04 with
scheduler constraints (Chapter 17) or use a *maintenance* drain whose reason references FAC-2210
(cancellable); record the event against the rack, not the nodes, so the nodes' repair history
stays clean.

**Common mistakes:** RMA-ing GPUs; treating `SW Power Cap` as the fault; no validation threshold;
a root cause that explains rack locality but not the daily cycle.
Source: Section 16.5 ("Thermals and burn-in"), runbook Table 16.7a (thermal row).

## Hardware run

The signals in this scenario can be reproduced on one GPU with `python scripts/hw_labs.py run ch16 --device gpu`
(and, read-only, with `ch19`). The burn-in samples `clocks_event_reasons.active` every 250 ms and decodes it, so
the learner sees `0x4` (SW Power Cap) at full load as the normal state and can check that the evaluator raises
`THERMAL_THROTTLE` only for a thermal reason or a temperature at or above 87 C. Rack inlet temperature and BMC
sensors are not available on a laptop. The rack-locality and time-of-day parts of the diagnosis stay L1/L3. With
`--device cpu` the run falls back to a CPU burn-in, and no clock-event reasons exist to decode.
