# Lab 9 — Congestion Telemetry Diagnosis (Progressive Lab 3)

## 1. Goal and the real-world task it mirrors

Halcyon AI's Training Infra team reports that W-TRAIN step times on ORION were erratic for ten
minutes. You are the Fabric on-call engineer. You have a telemetry bundle exported from the
collector: per-port switch counters, per-NIC RDMA congestion counters, pingmesh latency probes, the
topology, and the QoS configuration snapshot of the four switches involved. Your job is the one an
AI network engineer does after every congestion incident:

1. turn raw cumulative counters into trustworthy rates,
2. find the congestion episodes and classify each (incast, pause propagation, PFC storm),
3. locate the root of each congestion tree and any misbehaving device,
4. identify *victim* flows that suffered head-of-line (HOL) blocking without being congested themselves,
5. audit the QoS configuration against fabric intent,
6. use a small **SIMULATED** incast model to compare two documented configurations, and say what the
   simulation cannot conclude,
7. write the diagnosis report, experiment plan, and mitigation proposal (the Chapter 9 deliverable).

## 2. Tier and realism boundary

**Tier L1** (laptop, Python only, < 5 s runtime). The telemetry is synthetic and the incast model is
a fluid simulation. Nothing here measures a real switch ASIC, NIC, or DCQCN implementation. In
particular the 2 s sample interval hides microsecond-scale bursts (see manuscript Section 9.8), and
the model has no shared-buffer, multi-hop, or per-ingress-port PFC behaviour. Treat every
conclusion as a hypothesis to validate with the L3 extension.

## 3. Setup

```bash
cd book/part-3-networking/ch09-congestion-control-lossless-fabrics/lab
python -m pip install -r ../../../../requirements.txt     # numpy, pandas, pyyaml
python check.py                                           # progress meter for starter/congestion_lab.py
```

Python 3.10 or newer.

## 4. Background you need

| Topic | Manuscript section |
|---|---|
| Queue watermarks, shared buffers, sampling limits | 9.2, 9.8 |
| ECN marking profile (Kmin/Kmax/Pmax), BDP | 9.3 |
| PFC frames, Xoff/Xon, headroom | 9.4 |
| HOL blocking, pause propagation, storms, watchdog | 9.5 |
| DCQCN roles (RP/NP/CP) and the rate-cut rule | 9.6 |
| Incast arithmetic | 9.7 |
| Telemetry signatures table | 9.8 |

## 5. Data

| File | Contents |
|---|---|
| `data/switch_ports.csv` | `ts_s`, `switch`, `port`; gauges `tx_gbps`, `rx_gbps` (Gb/s over the interval), `q_tc3_max_kb` (maximum TC3 egress queue depth in the interval, KB); **cumulative** counters `ecn_marked_tc3` (packets), `pfc_tx_p3` / `pfc_rx_p3` (priority-3 pause frames sent to / received from the peer), `discards_tc3` |
| `data/nic_counters.csv` | per NIC: `tx_gbps`, `rx_gbps`; cumulative `cnp_sent` (as notification point), `cnp_handled` (as reaction point), `ecn_marked_rx`, `pfc_tx_p3`, `pfc_rx_p3` |
| `data/flow_probes.csv` | four pingmesh-style probes P1–P4: source/destination node, NIC and switch port; `lat_p50_us`, `lat_p99_us` |
| `data/topology.yaml` | links with roles (`downlink` = switch↔NIC, `fabric` = switch↔switch), `fabric_intent`, per-switch `qos` snapshot |
| `data/sim_configs.yaml` | common model parameters and three documented configurations |

Counter semantics follow switch conventions: on a port, `tx_*` is what *this* port sends toward its
peer. A non-zero `pfc_tx_p3` means this port asked its peer to stop sending priority 3 (the port's
ingress was filling); `pfc_rx_p3` means the peer asked this port to stop transmitting. The column
names are generic; Section 9.8 maps them to real NIC and switch counter families.

> **Pitfall:** the dataset is realistic, so it is not clean. Expect at least one counter that goes
> *backwards* and at least one device with missing samples.

## 6. Tasks

Implement the functions marked `TODO` in `starter/congestion_lab.py`. Helpers `load_dataset`,
`port_index`, `prepare_ports`, `_episode_stats`, `compare_configs`, and `run_analysis` are provided.

| # | Function(s) | Acceptance criterion |
|---|---|---|
| 1 | `counters_to_rates` | First sample NaN; gaps divided by true elapsed time; a negative delta (counter cleared) yields NaN, never a negative or invented rate. |
| 2 | `detect_episodes` | Hot = TC3 watermark ≥ 1,000 KB, or pause tx/rx ≥ 100 frames/s. Merge hot timestamps ≤ 6 s apart. A port that is merely busy (near line rate, shallow queue, ECN marks, no pause) must **not** produce an episode. |
| 3 | `classify_episode`, `find_roots` | Each episode labelled `incast`, `pause_propagation`, `pfc_storm`, or `unclassified` using the ordered rules in the docstring. A root is congested at ≥ 90 % of line rate and is *not* itself receiving pause. |
| 4 | `find_storm_source` | Names the device generating the storm as `node:nic`, confirmed from the NIC's own counters. |
| 5 | `find_victims` | Lists `(probe, episode)` pairs whose p99 latency inflated ≥ 10× while their destination port was uncongested. |
| 6 | `audit_qos` | Reports every deviation from fabric intent (codes in the docstring), with no false positives. BDP uses `fabric_intent.line_rate_gbps` and `base_rtt_us`. |
| 7 | `red_mark_probability`, `simulate_incast` | **SIMULATED** model obeys byte conservation, never beats the line-rate lower bound, and loses nothing when PFC is on and headroom suffices. |
| 8 | `build_report` | Markdown report with every heading in `REPORT_SECTIONS`, the simulation labelled `[SIMULATED]`, and the storm source named. |

When all checks pass, produce your report:

```bash
python starter/congestion_lab.py --out my_report.md
```

Then edit the generated report by hand: the code gives you the evidence tables; *you* write the
narrative (which hypothesis you rejected and why), the experiment plan, and the mitigation proposal.

### The documented configurations (Task 7)

| Config | PFC | ECN Kmin / Kmax / Pmax | Meaning |
|---|---|---|---|
| `A_as_found` | on (Xoff 1,000 KB, Xon 800 KB) | 1,500 / 6,000 KB / 0.2 | `orion-be-leaf-r3` as found in the snapshot |
| `B_template` | on (same) | 150 / 1,500 KB / 0.2 | the fabric template |
| `C_lossy` | off | 150 / 1,500 KB / 0.2 | lossy RoCE comparison (best-case selective retransmission after 20 µs; see manuscript Section 9.10) |

Common: 12 senders × 4 MB into one 400 Gb/s port, 4 µs ECN feedback delay, 1 µs PFC response,
4,000 KB port buffer share, 1,128 KB headroom (12 ingress ports × 93,496 B = 1,121,952 B ≈ 1,122 KB from the Section 9.4
formula for a ≈ 50 m cable, rounded up to 12 × 94 KB = 1,128 KB).

## 7. Running the checker

```bash
python check.py                    # your starter implementation
```

Each line is `PASS`, `FAIL` (with a hint), `TODO`, or `SKIP`. Diagnostic answers are stored as digests, so
the checker tells you *whether* you are right, not *what* the answer is. Exit code is 0 only when all
checks pass. (`data_determinism` is an instructor check; it reports SKIP when the dataset generator is
not shipped, which is normal in the student release.)

## 8. Deliverable and grading rubric (100 points)

Deliverable: **congestion diagnosis, experiment plan, and mitigation proposal** (one Markdown report,
≤ 3 pages, plus your code).

| Item | Points |
|---|---|
| Tasks 1–2: rates and episode detection correct (checker) | 15 |
| Tasks 3–4: classification, roots, storm source (checker) | 20 |
| Task 5: victim flows (checker) + explanation of why each is a HOL victim | 10 |
| Task 6: QoS audit (checker) + consequence of each finding in one sentence | 10 |
| Task 7: simulation results table, correctly labelled `[SIMULATED]`, with a "cannot conclude" list of ≥ 4 specific items | 15 |
| Diagnosis narrative: ranked hypotheses, the discriminating evidence for each episode, proven vs. correlated | 15 |
| Experiment plan: one variable, ≥ 5 repetitions, warm-up, counters, manifest, safety boundary | 10 |
| Mitigation proposal: ordered, safe (canary/rollback), validation criteria | 5 |

## 9. Extensions

### L2 (any Linux host with an RDMA-capable NIC, read-only)

Map the lab's generic columns to your NIC's real counters and capture a baseline. On mlx5-class
NICs (verify names against your driver's counter documentation):

```bash
ethtool -S <netdev> | grep -E 'prio3_pause|pause_storm'      # rx/tx_prio3_pause, *_pause_duration, tx_pause_storm_*_events
rdma statistic show link <rdma_dev>/1                         # includes np_cnp_sent, rp_cnp_handled, np_ecn_marked_roce_packets
cat /sys/class/infiniband/<rdma_dev>/ports/1/hw_counters/np_cnp_sent
```

Record the values twice, 60 s apart, and compute rates with your `counters_to_rates`.

### L3 (dedicated lab fabric only — never production)

> **Safety:** run only on an isolated lab fabric you are authorised to change. Incast tests saturate
> buffers and trigger PFC on every hop that carries the lossless class.

1. Snapshot the switch QoS configuration (trust mode, DSCP→TC map, PFC priorities, ECN profile,
   PFC watchdog state) and the NIC QoS state (`mlnx_qos -i <netdev>` or `dcb pfc show dev <netdev>`).
2. Build an N:1 incast with perftest: on the receiver, start N servers on distinct ports
   (`ib_write_bw -d <rdma_dev> -x <gid_index> -p <port_k> -s 65536 -D 30 --report_gbits`);
   on each of N senders, the matching client with the receiver's address. Warm up 10 s; discard.
3. Collect at ≤ 1 s intervals during each run: switch egress queue watermark for the receiver port,
   ECN-marked packets, pause frames tx/rx on every involved port, NIC `np_cnp_sent`/`rp_cnp_handled`,
   and per-client bandwidth.
4. Configuration A vs B: change **only** the ECN thresholds on the lab leaf between runs; ≥ 5
   repetitions each; report median and p95/p99 of per-flow bandwidth and of pause duration, with
   min/max spread.
5. Compare the direction of change with the SIMULATED result. Explain any disagreement using the
   "cannot conclude" list.
6. Fill a copy of `manifest.yaml` with the real values listed under `extensions[].record`.

## 10. Intentionally flawed inputs

The dataset contains planted anomalies and configuration faults. They are documented for instructors
in `solutions/exercises-key.md` (Lab section), not here.
