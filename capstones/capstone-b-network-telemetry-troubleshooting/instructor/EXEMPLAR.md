# Capstone B — Exemplar Summary (abridged, distinction level)

INSTRUCTOR ONLY. Abridged summary of what a 90+ submission contains, written as the learner would
write it. All results are `[SIMULATED]` (the supplied capture) unless marked otherwise.

## 1. Problem and success criteria

On-call goal: page the Fabric team once per real fabric problem, naming the root-cause device, and never
during approved changes. Targets on the supplied capture: recall 1.0 and precision ≥ 0.9. With five
injected faults, that means zero false pages. Pages are scored by when they fire, against each
fault's [onset, onset + tolerance] window. Detection latency is reported from onset. Five positives
cannot estimate a production false-positive rate. They show the mechanisms only.

## 2. Architecture

Three collectors (leaf CLI poller, spine gNMI subscriber, host agent) write native records. A
normalizer emits `(ts UTC, device, interface, canonical counter, native name, value, source)`. A rate
stage applies per-platform widths from `device_profiles.yaml`. A rule engine evaluates per-port and
per-leaf rules with persistence, with suppression from the change calendar extended to link peers via
`topology.csv`. Alerts carry an evidence sentence and link to the runbook section. Meta-monitoring
covers source staleness, reset storms and unplanned `clear counters`.

## 3. Schema decisions worth noting

- Pause counters are named from the reporting interface's point of view: `pfc_rx_pause_p3` = pause
  frames *received* (the peer is asking us to stop). A host NIC with a high `tx_prio3_pause` is
  *causing* back-pressure.
- ECN is two counters, not one. The switch counts packets it *marked* on egress (`ecn_marked_p3`). The
  NIC counts CE-marked packets it *received* as the notification point (`ecn_ce_received_p3`, from
  `np_ecn_marked_roce_packets`).
- `native` is kept for lineage and width lookup. Leaf `RxPause3/TxPause3` are 32-bit.
- Wrap vs reset: a decrease is a wrap only on a 32-bit counter whose previous value was ≥ 2³¹ **and**
  whose implied rate is under the platform's plausibility bound (2 × 10⁶ pause frames/s). Otherwise it is
  a reset, and the interval is invalid (NaN), never 0 and never `cur`. In production we would key on a
  discontinuity signal (device uptime or boot ID) instead. Three resets appear in the capture (orion-n30,
  orion-be-leaf-r7, orion-be-spine-2). The spine-2 clear is not in the change calendar, which produces
  a backlog item.
- FEC: healthy ports correct ≈ 1.5 × 10⁵ codewords/s, so we page on FCS/uncorrectable counts only. The
  corrected-codeword trend (> 5× the port's own baseline for 2 intervals) is an early warning, and we
  ask the vendor for pre-FEC BER and symbol-error histogram bins.

## 4. Results

| Fault (onset) | Rule | Paged at | Latency from onset |
|---|---|---|---|
| ECN disabled, orion-be-leaf-r6 (10:00) | ecn_misconfig (peer comparison, 3 intervals, hysteresis 3) | 10:03:01 | 181 s |
| ECMP polarization, orion-be-leaf-r1 (10:00) | ecmp_imbalance (CV > 0.5, 3 intervals) | 10:03:01 | 181 s |
| Host CRC, orion-n24 mlx5_2 (10:11) | link_degradation (FCS > 0, 2 NIC polls) | 10:14:03 | 183 s |
| PFC storm, orion-n17 mlx5_5 (10:15) | pfc_storm (≥ 10,000/s received, 3 intervals) | 10:18:02 | 182 s |
| Receive degradation, orion-be-leaf-r2 Ethernet1/50 (10:04) | early warning 10:15:01 (FEC trend); page on FCS | 10:19:01 | 901 s |

Precision 1.00, recall 1.00 (5 TP, 0 FP, 0 FN, 0 duplicates). Hysteresis matters: without it the
ECN rule re-fires at 10:15 after the checkpoint burst briefly raises the peer median. That would be a
second page for the same fault.

**Persistence sweep:** persistence 1 gives 5 TP and 195 FP (precision 0.025). 192 of those are pages for
the 10:12 checkpoint burst, including orion-n17 mlx5_5 three minutes before its real storm, and 3 are
single FCS glitches. Persistence 2–5 gives 0 FP, with worst-case latency 901, 962, 1,022 and 1,081 s.
We deploy persistence 2 for physical-layer errors and 3 for PFC, ECN and ECMP. At 3 minutes, the
192-GPU W-TRAIN job loses ≈ 3 min × 192 GPUs ≈ 9.6 GPU-hours before the page `[MODELED]`. We accept that
against 192 false pages per checkpoint burst.

**Threshold sweeps:** the PFC threshold works from 2,000 to 20,000 frames/s, and 60,000/s misses the
storm (peak ≈ 54,000/s). We chose 10,000/s: healthy host ports sit near 3/s, the benign burst peaks
near 16,500/s for one interval, and the storm sits near 50,000/s. Persistence, not the threshold,
separates the burst from the storm. The ECMP CV threshold works from 0.2 to 0.8. Healthy leaves sit at
0.07–0.08, and maintenance-induced skew reaches ≈ 0.27 (leaf r7 with two uplinks down).

## 5. Incident report excerpt (PFC storm)

*Symptom:* rail-5 throughput fell to ≈ 45 % of the other rails from 10:15, and 31 leaf-r5 host ports
began sending pause (`TxPause3` ≈ 2,000–2,700/s). *Hypotheses ranked:* (1) one receiver not draining,
(2) leaf-r5 buffer misconfiguration, (3) a congested spine. *Discriminating evidence:* exactly one
leaf-r5 port *receives* storm-level pause (Ethernet1/17 ≈ 50,000/s). Its peer NIC, orion-n17 mlx5_5,
shows `tx_prio3_pause` ≈ 50,000/s and receive bytes collapsed to ≈ 0.02 GB/s. The spine uplinks show
only moderate pause (≈ 600/s), and the other rails are normal. *Root cause (proven at counter level):*
the orion-n17 rail-5 receive path stopped draining. *Correlation only:* why it stopped. Host
evidence (kernel log, GPU Xid, NIC firmware events) is not in the capture. *Actions:* drain
orion-n17 in Slurm (this stops new placement but does not move the running job). Then checkpoint and
restart W-TRAIN without it. ORION has no spare nodes, so the restart runs at reduced DP: DP 6 → 5 on the
24-node partition (20 nodes used, 3 idle). The 1,152-sequence global batch does not divide by 5, so the
restart uses 960 sequences (192 per replica) with a learning-rate adjustment. The ≈ 900 s restart cost
is preferred to running with rail 5 paused. Enable the
switch's PFC watchdog on host-facing ports (vendor feature, change-controlled), and add the host-side
evidence collection to the runbook.

## 6. Added scenario

We added a "slow-drain receiver" to a copy of the generator: one host NIC sends pause at 3,000/s
(below the storm threshold) for 15 minutes. No existing rule fires. A new rule, "pause received on a
host port > 20× that leaf's median host port for 5 intervals", detects it with no FP on the original
capture. It is documented as a P1 rule pending a production baseline.

## 7. Security and operations highlights

Collectors use read-only accounts; gNMI uses TLS with per-device certificates. The change calendar is
an input that can silence pages, so writes to it are audited and need a ticket. Telemetry retention
is 30 days, with access restricted to Fabric and SRE because it reveals tenant traffic patterns. The
meta-alerts are a source silent for more than 3 polls, more than 3 resets on a device in 10 minutes,
and any `clear counters` outside a change window.

## 8. Backlog (top 3)

1. **P0:** re-baseline every threshold on two weeks of production counters (p99.9 per rail, per port
   role) before enabling pages, and replace the wrap heuristic with device-uptime discontinuity signals.
2. **P0:** L3 validation: an incast with ECN disabled on a lab switch, five repetitions, with measured
   detection latency.
3. **P1:** correlate alerts with the scheduler's rank-to-node map so each page lists the affected job.
