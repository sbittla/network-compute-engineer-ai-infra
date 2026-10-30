# Capstone B starter kit: an ORION fabric telemetry and troubleshooting pipeline

You will build the core of the system Halcyon AI's Fabric team uses to find RoCEv2 fabric problems
before the training team does. The pipeline parses counters in three native formats, normalizes them
into one schema, turns cumulative counters into rates without being fooled by wraps and resets, and
runs alert rules. The rules attribute each problem to its root-cause device rather than to the twenty
ports that show symptoms, and they stay quiet during planned maintenance and benign bursts. The checker
scores your alerts for precision and recall against hashed ground truth.

> **Realism boundary:** The capture is `[SIMULATED]` by a counter generator driven by a simple traffic
> model. It reproduces the *signatures* engineers look for: pause-rate storms, PFC without ECN, FEC
> ramps before FCS errors, ECMP skew, wraps and resets. It does not model switch buffers, PFC/ECN
> control loops, NIC firmware or telemetry-transport loss. Thresholds tuned here are a starting point.
> On real hardware they must be re-baselined, and Section 8 shows how.

## 1. Goal and the real-world task it mirrors

On-call fabric engineers rarely lack data; they lack data they can trust and alerts they can act on.
This kit mirrors the work of turning a heterogeneous counter feed into a small number of correct,
evidence-carrying alerts. The leaf vendor emits CLI text, the spine vendor streams JSON, and host
agents dump `ethtool -S`. The capture covers ORION-256's backend fabric for 30 minutes while W-TRAIN runs on the default
24-node training partition (`orion-n01`–`n24`) and `orion-n25`–`n32` serve inference (light backend traffic).
Several things go wrong in it, and several things look as if they went wrong but did not.

## 2. Tier and realism

| Tier | What you do | Evidence class |
|---|---|---|
| L1 (required) | Implement `starter/telemetry.py`; pass `check.py`; write the artifacts | `[SIMULATED]` |
| L2 (optional) | Run your parser against real `ethtool -S` and RDMA hw_counters from one lab host | `[MEASURED]` counters from that host |
| L3 (optional) | Reproduce a congestion signature (incast) on a lab fabric and detect it with your rules | `[MEASURED]` on that lab fabric |

## 3. Setup

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -r ../../../requirements.txt                  # numpy, pandas, pyyaml (Python >= 3.10)
# (instructor edition only) python tools/generate_data.py regenerates data/ byte-identically
python check.py                                           # progress meter
```

## 4. The bundle (`data/`)

| Path | Contents |
|---|---|
| `leaf_cli/orion-be-leaf-r{0..7}.txt.gz` | Rail leaves, CLI text tables, ~60 s polls, 64 ports each |
| `spine_stream.jsonl.gz` | Four spines, one JSON record per device per ~60 s poll |
| `nic/orion-n{01..32}.txt.gz` | Host-agent dumps for 8 NICs per host, ~120 s polls |
| `topology.csv` | Every backend link: leaf port ↔ host NIC (`host`), leaf uplink ↔ spine port (`fabric`) |
| `device_profiles.yaml` | Format, timestamp encoding, poll interval and **counter widths** per platform |
| `maintenance.yaml` | The change calendar for the capture window |
| `ground_truth.sha256` | SHA-256 of each injected root-cause fault key (the checker's answer key, hashed) |

Excerpts (`zcat` or `gzip -dc` the files to read them):

```text
orion-be-leaf-r4# show interfaces counters
Timestamp: 2026-10-12T10:00:02Z
Port              InOctets        OutOctets  InDiscards  OutDiscards  FCSErrors  FECCorrected  FECUncorr    RxPause3    TxPause3  EcnMarked3
Ethernet1/1   465052193260790  402179902675241       41          6         38   60658446720        23   857678703  1420297829  81895853394
```

```json
{"timestamp_ns":1791799202695813120,"device":"orion-be-spine-1","updates":[{"path":"/interfaces/interface[name=Ethernet1/1]/state/counters","values":{"in-octets":870996978510543,"out-octets":482730710749222,"in-discards":0,"out-discards":4,"in-fcs-errors":0}},{"path":"/qos/interfaces/interface[name=Ethernet1/1]/ext/pfc-ecn","values":{"rx-pause-3":505459904,"tx-pause-3":2012662019,"ecn-marked-3":14502417223}}]}
```

```text
### collected_at=1791799205 host=orion-n24 dev=mlx5_0 netdev=ens0np0 rail=0
NIC statistics:
     rx_vport_rdma_unicast_bytes: 13360772839046
     rx_prio3_pause: 33688797
     rx_crc_errors_phy: 3
RDMA hw_counters (/sys/class/infiniband/mlx5_0/ports/1/hw_counters):
     np_cnp_sent: 9277648476
     np_ecn_marked_roce_packets: 2879134950
     out_of_sequence: 869
```

The switch formats are vendor-neutral renderings: real network operating systems differ in command
names and column labels. The NIC counter names follow the Linux mlx5 driver's `ethtool -S` output and
the RDMA `hw_counters` directory `[VENDOR-SPEC, 2026-10]`. Names vary by driver and firmware version,
so verify against your own hosts.

## 5. Background you need

- PFC, ECN, DCQCN and what a pause storm looks like: [Chapter 9](../../../book/part-3-networking/ch09-congestion-control-lossless-fabrics/).
- RoCEv2 counters (CNPs, out-of-sequence, ACK timeouts): [Chapter 8](../../../book/part-3-networking/ch08-rdma-rocev2-infiniband/).
- FEC, FCS, optics degradation: [Chapter 10](../../../book/part-3-networking/ch10-switches-optics-physical-layer/).
- ECMP and rail-optimized fabrics: [Chapter 7](../../../book/part-3-networking/ch07-ethernet-datacenter-network-foundations/).
- Alert design, SLOs, false positives, incident reports: [Chapter 18](../../../book/part-5-production-operations/ch18-observability-slos-incident-response/).

## 6. Tasks (100 points)

| # | Task | Acceptance criterion | Points |
|---|---|---|---|
| 1 | Fill the three native→canonical maps and implement the three parsers | Checks 01–04 pass; `templates/telemetry-schema.md` documents every field, unit and lineage | 15 |
| 2 | `counter_delta`, `compute_rates`: wrap- and reset-aware rates using real `dt` and per-platform widths | Checks 05–06 pass; the schema doc explains your wrap/reset policy | 15 |
| 3 | `in_maintenance` and `detect`: the five rule families, persistence, peer comparison, and suppression that also covers link peers | Checks 07–11 pass | 25 |
| 4 | `score` and `leaf_health_table` | Checks 12–13 pass | 5 |
| 5 | False-positive analysis: precision/recall versus persistence (1–5) and versus each rule's main threshold; explain each FP class | `templates/false-positive-analysis.md` with tables and reasoning | 15 |
| 6 | Runbook for each fault class and an incident report for the most severe fault in the capture | `templates/runbook.md`, `templates/incident-report.md` | 15 |
| 7 | Report or dashboard specification built from `leaf_health_table` and your alerts | `templates/dashboard-report-spec.md`, with at least one rendered chart or table | 10 |

Suggested rule logic is in the docstring of `detect`. Your rules may differ, as long as you justify every
threshold with evidence from the data, not with "it made the checker pass".

## 7. Running the checker

```bash
python check.py                    # your starter implementation
python check.py --impl solution    # instructor edition only
```

The checker scores pages by **when they fire** (`fired_ts`). A page counts only inside the fault's
[onset, onset + tolerance] window; a page before onset is a false positive. With five faults, precision
≥ 0.9 means zero false pages. The checker prints recall, precision and latency, but never which faults
you missed. Use your own evidence to
find them. That is the job.

## 8. Extensions: hardware-backed validation (L2/L3)

> **Safety:** Generate congestion only on a dedicated lab fabric with no other tenants. Never change
> PFC/ECN/QoS settings or run incast tests on shared or production switches.

### L2: real NIC counters on one host

```bash
ethtool -S <netdev> | grep -E 'prio3_pause|discards_phy|crc_errors_phy|vport_rdma'
ls /sys/class/infiniband/mlx5_0/ports/1/hw_counters/
cat /sys/class/infiniband/mlx5_0/ports/1/hw_counters/np_cnp_sent
rdma statistic show link mlx5_0/1                    # iproute2 rdma tool, where supported
mlnx_qos -i <netdev>                                 # PFC enablement and trust mode (vendor tool, where installed)
```

Write a small collector that emits your NIC format every 10 s for 10 minutes, run your parser on it,
and record which canonical counters exist under which native names on your driver and firmware.

### L3: validate a congestion signature on a lab fabric

1. Stream switch counters, for example with gNMI:
   `gnmic -a <switch>:<port> --username <u> --password <p> subscribe --path /interfaces/interface/state/counters --mode stream --stream-mode sample --sample-interval 10s`,
   or poll the switch CLI if gNMI is not available. Your switch's PFC/ECN counters may sit under a
   vendor-specific path. Check the vendor's YANG models.
2. Create an incast: run several `ib_write_bw` clients (perftest) on different hosts against one server
   for 60 s. Then repeat with ECN marking disabled on the lab switch's lossless queue, *only on that lab
   switch*.
3. Confirm that your rules fire for the ECN-disabled case and not for the normal incast. Record
   detection latency, precision and recall over at least five repetitions, and the manifest fields in
   `manifest.yaml`.

## 9. Deliverable

All templates in [`../templates/`](../templates/) filled in, your `telemetry.py`, and the outputs of
the checker. The injected faults and benign traps are documented for instructors only.
