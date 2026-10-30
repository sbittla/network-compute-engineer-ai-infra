# Lab 10 — Link-Health Analyzer and Physical-Layer Commissioning for an ORION Rail Leaf

## 1. Goal and the real-world task it mirrors

A new rail leaf, `orion-be-leaf-r3`, has been cabled and powered. Before the Fabric team enables
routing on it, someone must answer: *which of its 64 links are physically fit for service, which
need a technician, and which look bad for reasons that have nothing to do with optics?* The same
question is asked during every incident that starts with "is it the network?".

You will build the tool a fabric engineer builds in their first month on an AI cluster:

- difference two snapshots (T0 and T0 + 600 s) of per-port counters and DOM readings, correctly;
- classify every port as **physical**, **higher_layer**, or **healthy**, with a primary finding,
  severity, and action;
- produce a **commissioning report** suitable for a change ticket;
- do the supporting arithmetic (KP4 line rate, FEC margin, link budget);
- estimate **ports, optics, cables, and spares** for a small leaf-spine fabric and for ORION, and
  generate a labeled **cabling schedule**.

## 2. Tier and realism boundary

**Level 1** (laptop; Python only; no hardware, no network, no root). The dataset is `[SIMULATED]`:
values are modeled on ORION and on the counter semantics in the manuscript, not captured from a
switch. The thresholds in `data/thresholds.yaml` are `[ILLUSTRATIVE]` fleet policy, not vendor
limits. This lab cannot show real SerDes behaviour, real FEC burst statistics, DOM accuracy, or how a
particular NOS names and stomps counters — see the L2/L3 extensions.

## 3. Setup

```bash
cd book/part-3-networking/ch10-switches-optics-physical-layer/lab
python -m pip install -r ../../../../requirements.txt     # pandas, pyyaml (numpy etc.)
python check.py                                           # starter: shows TODOs
```

Python 3.10+. Edit only `starter/linkhealth.py`. Treat `data/` as read-only evidence. (The dataset
generator is instructor copy only; in the student release the reproducibility check reports SKIP.)

## 4. Background you need

| Topic | Manuscript section |
|---|---|
| Counter-to-layer map; physical vs higher-layer tests | 10.8, Table 10.6 |
| PAM4, KP4 FEC, line rate, pre-FEC BER margin | 10.4, Table 10.1 |
| DOM and receive-power patterns | 10.6.3, 10.7 |
| Link budget arithmetic | 10.6.2 |
| Cabling schedules, LLDP validation | 10.10 |
| Commissioning gates and checklist | 10.11, Table 10.8 |
| Sparing | 10.12 |

## 5. Data

| File | Contents |
|---|---|
| `data/snapshot_t0.csv`, `data/snapshot_t1.csv` | One row per port: status, MTU, installed optic type and serial, LLDP neighbour, cumulative counters (link-down events, frames, FCS errors, oversize frames, output discards, ECN marks, PFC pause rx/tx, FEC corrected and uncorrectable codewords), pre-FEC BER, module temperature, and per-lane Tx bias, Tx power, Rx power (lanes 0–3). Counters are cumulative; DOM values are instantaneous. |
| `data/cabling_schedule.csv` | Intended topology: cable ID, both endpoints, expected optic at each end, media, length, labels. |
| `data/thresholds.yaml` | Pre-FEC BER policy (warn 1e-5, critical 1e-4, KP4 limit 2.4e-4); per-optic Rx policy (DR4: warn −4.0 dBm, critical −5.9 dBm = receiver minimum) plus the module-programmed −6/−9 dBm thresholds for reference only, temperature, BER rising factor 10, flap and lane-imbalance limits, PFC rate limit. |
| `data/fabrics.yaml` | Two fabric specs (`small`: 16 nodes; `orion`: 32 nodes) and a spares policy. |

Each 400G port is modeled with its own module (single-port DR4 per OSFP cage, the manuscript's
ORION assumption). Uplinks Ethernet33–64 go to spines 1–4 (8 each); host links Ethernet1–32 go to
`orion-n01`…`orion-n32` (node `orion-nNN` on leaf port `EthernetNN`), NIC3.

## 6. Tasks

| # | Function(s) in `starter/linkhealth.py` | Acceptance criterion (checked) | Points |
|---|---|---|---|
| 1 | `counter_delta`, `pcs_fec_line_rate_gbps`, `fec_margin_decades` | Reset-aware deltas; 400G → 425.0 Gb/s; margin(2.4e-6) = 2.0 decades | 10 |
| 2 | `compute_deltas` | 64 ports, `dt_s` = 600, no negative deltas, `d_*` columns for every counter | 10 |
| 3 | `classify_port`, `analyze` | Layer counts, primary-finding counts, per-port digest and severity policy all match the reference | 35 |
| 4 | `commissioning_report` | Overall FAIL; 57/64 accepted; every failing and referred port named in the Markdown | 10 |
| 5 | `link_budget` | Nominal and worst-case DR4 budgets match | 5 |
| 6 | `estimate_fabric_bom` | Small fabric and ORION: leaves, spines, links, optics, cables, spares | 10 |
| 7 | `generate_cabling_schedule` | Correct row count, unique cable IDs and endpoints, even leaf–spine spread, labels name both ends | 10 |
| 8 | Written diagnosis (`diagnosis.md`) | For every non-healthy port: evidence, layer, root-cause hypothesis, first safe action, and the evidence you would still collect on hardware. Explain why any decoy you found is *not* a fault. | 10 |

Expected checker output when complete: `13/13 checks passed`. You may also write the report:

```bash
python check.py --report commissioning-report.md
```

## 7. Running the checker

```bash
python check.py                    # your starter implementation
python check.py --impl solution    # instructors: reference implementation
```

Each line is `PASS`, `FAIL` (with the reason), or `TODO` (function still raises
`NotImplementedError`). The per-port answers are stored as a digest so the checker does not give
away the diagnosis; use the count hints and your own reasoning.

## 8. Deliverable and grading rubric (100 points)

Submit: `starter/linkhealth.py`, `commissioning-report.md`, `diagnosis.md`, and your physical-layer
runbook and port/cabling schedule for the small fabric (the chapter deliverable; see
`../exercises.md`, Exercise 10.M4). Points per task are in the table above (90 automated + 10 for the
written diagnosis). Deduct up to 10 points for a diagnosis that calls a higher-layer port "physical"
or recommends touching a production link without a drain.

## 9. Extensions: hardware-backed variants

> **Safety:** Run these only on a dedicated lab switch and lab hosts, never on a production fabric.
> Do not reseat, unplug, or admin-down links that carry other people's traffic.

**L2 (one host, one NIC port).** Collect two snapshots 600 s apart while running a steady load
(e.g., `ib_write_bw` from the perftest suite or `iperf3` to a peer):

```bash
sudo ethtool -m <ifname>                 # DOM: temperature, bias, Tx/Rx power per lane, thresholds
ethtool -S <ifname> > t0.txt             # driver counters (names vary by driver)
ethtool --show-fec <ifname>              # configured/active FEC mode
ethtool -I --show-fec <ifname>           # FEC statistics, if supported by driver and kernel
ip -s -s link show dev <ifname>
# wait 600 s, repeat into t1.txt
```

Map your driver's counter names onto the dataset columns (manuscript Table 10.6), convert to the CSV
schema, and run your analyzer. NVIDIA NICs with MFT installed can also use `mlxlink -d <device> -m`
(module) and `mlxlink -d <device> -c` (counters); check `mlxlink --help` for your version.

**L3 (lab leaf + hosts).** On the switch, capture both ends of every link at T0 and T0 + 600 s under
load: the NOS transceiver/DOM view (e.g., Arista EOS `show interfaces transceiver`, SONiC
`show interfaces transceiver eeprom --dom`), error counters (EOS `show interfaces counters errors`,
SONiC `show interfaces counters`), PHY/FEC detail where available (EOS `show interfaces <intf> phy
detail`), and LLDP neighbours (`show lldp neighbors`). Inspect every end-face and record the result.
Then, **on a lab link only**, introduce one controlled fault at a time — e.g., swap two jumpers
(miscabling), set one port's MTU to 1500 (giants), insert a known-attenuation inline attenuator if
your optic vendor permits it (low Rx) — and confirm your analyzer's classification changes as
predicted. Record everything listed under `extensions` in `manifest.yaml`, plus ≥ 5 repeated
snapshot pairs per condition, and report median and spread of the pre-FEC BER.

## 10. Intentionally flawed inputs

The dataset contains planted faults and decoys. They are documented for instructors only in
`../solutions/exercises-key.md` (section "Lab answer key"). Do not look there before you have
written your diagnosis.
