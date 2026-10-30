# Lab 7 — Fabric Design and Validation Tool (Progressive Lab 2)

## 1. Goal and the real-world task it mirrors

Before a fabric is cabled, a fabric engineer sizes it, writes the addressing and BGP plan, and —
before every change afterwards — validates the *intent* (the source-of-truth data that generates
device configurations) so that a typo never reaches a switch. You will build that tool for the
ORION-256 backend: compute leaf/spine counts and cabling from port assumptions, generate the /31
addressing plan and eBGP neighbor table, then run your validator against a supplied fabric intent
that contains real-world classes of error, and quantify capacity after link, spine, and leaf failures.

This is **Progressive Lab 2 — Fabric design** of the 14-week course (week 4).

## 2. Tier and realism boundary

**Tier L1** (laptop): standard-library Python ≥ 3.10, no network, no root, < 1 s runtime.

> **Realism boundary:** Everything here is `[MODELED]` or static analysis. The lab cannot show real
> ECMP hash behaviour, queueing, convergence timing, or how a particular NOS interprets "MTU". It
> proves your *reasoning and tooling*; the L2/L3 extensions (Section 8) are where behaviour is
> measured.

## 3. Setup

```bash
cd book/part-3-networking/ch07-ethernet-datacenter-network-foundations/lab
python --version                         # 3.10 or newer
python check.py                          # starter: everything reports TODO, exit code 1
```

No third-party packages are required (the repository `requirements.txt` is a superset).

## 4. Background you need

- Manuscript Section 7.3 (addressing, Table 7.2) and Section 7.5 (ASN plan, `maximum-paths`,
  advertisements).
- Section 7.4 (MTU) and Section 7.7 (Clos arithmetic, rail-optimized design).
- Section 7.9 and Section 7.10, Table 7.8 (capacity after failure; ECMP-aware ingress).

### Intent conventions (the contract your validator enforces)

| Item | Convention |
|---|---|
| Names | `orion-be-leaf-r0`…`orion-be-leaf-r7` (rail r), `orion-be-spine-1`…`orion-be-spine-4`, hosts `orion-n01`…`orion-n32` |
| Host link (rail r, node n = 1..32, i.e. `orion-nNN`) | leaf `Ethernet<n>` = `10.100.r.(2n)/31`; host `nic<r>` = `10.100.r.(2n+1)/31` |
| Fabric link (leaf r, spine s, link k = 0..7) | idx = 8r + k; spine `Ethernet<1+idx>` = `10.101.s.(2·idx)/31`; leaf `Ethernet<33+(s−1)·8+k>` = `10.101.s.(2·idx+1)/31` |
| ASNs | all spines 65100 (shared on purpose, RFC 7938); `orion-be-leaf-r<r>` = 65101 + r |
| MTU | fabric links 9216 on both ends; host links switch 9216 / host 9000 |
| Ownership | a leaf owns exactly `10.100.r.0/24` and its loopback `/32`; it must advertise both to every spine it has a link to, and nothing else |

### Data files (`data/`; generator is instructor copy only)

| File | Rows | Columns |
|---|---|---|
| `devices.csv` | 12 | device, role, rail, asn, loopback, ecmp_max_paths |
| `links.csv` | 512 | link_id, link_type (host/fabric), a_device, a_port, a_ip, a_mtu, b_device, b_port, b_ip, b_mtu, speed_gbps |
| `advertisements.csv` | one per (leaf, spine, prefix) | device, neighbor, prefix |

Rows are shuffled deliberately; do not rely on order.

## 5. Tasks

Implement the TODO functions in `starter/fabric_lab.py`. Docstrings define every return key.

1. **Size the fabric** — `size_two_tier(endpoints, leaf_ports, spine_ports, oversub)`.
   *Acceptance:* ORION (256, 64, 64, 1:1) → 8 leaves, 4 spines, 8 links per pair, 512 cables,
   1,024 transceivers; the frontend pair (48 × 200G down / 16 × 400G up: 3:1 by ports, 1.5:1 by bandwidth — use
   `down_gbps=200`) and the ORION-XL radix question pass (T1a–T1c).
2. **Generate the addressing plan** — `build_addressing_plan()`: 512 rows, unique /31s.
   *Acceptance:* T2a–T2b; e.g. `F-r2-s3-k1` = spine `10.101.3.34/31`, leaf `10.101.3.35/31`, leaf
   port `Ethernet50`, spine port `Ethernet18`.
3. **Generate the eBGP neighbor table** — `build_bgp_neighbors(plan)`: 256 sessions, 32 per leaf,
   64 per spine. Save it as `bgp_neighbors.csv` for your deliverable. *Acceptance:* T3.
4. **Validate the supplied intent** — `validate_intent(load_intent("data"))`. Find every planted
   error with the exact codes in the docstring and **no false positives** (spines sharing AS 65100
   and hosts at MTU 9000 are correct). For each finding, write one line in your report: what it is,
   its operational consequence on ORION, and its severity. *Acceptance:* the seven T4 checks.
5. **Capacity after failure** — `fabric_capacity(link_counts, link_gbps, advertised)`.
   *Acceptance:* T5 (baseline 12,800 / 12,800 / 51,200 Gb/s; one link down 12,400 / 11,200 / 50,800;
   spine down 9,600 / 9,600 / 38,400; unadvertised prefix 12,800 / 9,600 / 51,200; leaf down
   0 / 0 / 38,400). Then compute the capacity consequence of **each** planted fault that has one.
6. **Design note (deliverable)** — ≤ 2 pages: topology diagram (Mermaid is fine), routing-policy
   summary (ASNs, origination, prefix filters, `maximum-paths`, BFD/BGP timers, drain procedure),
   and a failure-convergence table (link, spine, leaf: detection → convergence → capacity →
   workload impact), with every number traced to your tool and labelled `[MODELED]`.

**Stretch (Exercise 7.L):** specify a `QOS_MISMATCH` rule (DSCP trust, DSCP→class map, lossless
priority) and the intent fields it needs.

Expected solution output (abridged):

```text
[blocker] DUP_P2P        10.101.3.72/31   /31 used on 2 links: ...
[blocker] ASN_COLLISION  65107            ASN shared by ...
...
```

## 6. Running the checker

```bash
python check.py                    # your starter implementation
python check.py --impl solution    # instructors only (needs ../solutions/lab/)
```

One line per check — `PASS`, `FAIL` (with a reason or hint), or `TODO` (function still raises
`NotImplementedError`). Check T0 (data integrity) reports `SKIP` in the student release, where the
generator is instructor copy only; do not edit `data/` by hand. Exit code 0 only when every non-skipped check passes. Runs from
any directory.

## 7. Deliverable and grading rubric (100 points)

| Component | Points | Full marks when |
|---|---|---|
| Task 1 sizing | 10 | T1a–T1c pass; you can explain `feasible=False` for ORION-XL at radix 64 |
| Task 2 addressing | 10 | T2a–T2b pass; plan exported as CSV |
| Task 3 BGP table | 10 | T3 passes; exported as CSV |
| Task 4 validation | 25 | All planted findings, zero false positives, each with consequence and severity |
| Task 5 capacity | 15 | T5 passes; consequence of each planted fault quantified |
| Task 6 design note | 25 | Diagram, routing policy, failure-convergence table; all numbers traced and labelled |
| Code quality | 5 | Type hints, docstrings with units, no global mutable state |

## 8. Extensions (L2 / L3)

### L2 — container fabric (one Linux host)

Build a 2-spine × 4-leaf eBGP fabric with containerlab and FRRouting containers, generated from your
addressing plan (scale the plan down; keep the conventions). Then, **on that isolated lab only**:

```bash
sudo containerlab deploy -t orion-mini.clab.yml
docker exec -it clab-orion-mini-leaf-r0 vtysh -c "show bgp ipv4 unicast summary"
docker exec -it clab-orion-mini-leaf-r0 vtysh -c "show ip route 10.100.3.0/24"   # count next hops
docker exec -it clab-orion-mini-leaf-r0 vtysh -c "show bfd peers"
# Fail one link inside the lab and time reconvergence from a host container:
docker exec clab-orion-mini-leaf-r0 ip link set eth3 down
docker exec clab-orion-mini-h0 ping -i 0.01 -c 2000 10.100.3.1 | tail -3   # count lost probes x 10 ms
```

Repeat each failure ≥ 5 times; report median and max loss window, with and without BFD. Re-create
two planted faults (an ASN collision, `maximum-paths 1`) and capture the evidence they produce
(`show bgp ipv4 unicast <prefix>`, next-hop counts). Container dataplanes do not model ASIC hashing
or buffers — label results `[SIMULATED]`.

### L3 — dedicated physical lab fabric

On a non-production leaf-spine with ≥ 2 RoCEv2 hosts: verify MTU end to end with
`ping -M do -s 8972` **and** a multi-source-port sweep (`iperf3 --cport`), confirm the RDMA active
MTU with `ibv_devinfo`, measure ECMP spread with per-uplink counters while running multiple
`ib_write_bw` streams (from `perftest`; e.g. `ib_write_bw -d <dev> -q 8 --report_gbits <server>`),
and time BFD-detected failover. Change one variable per run.

**Record in your copy of `manifest.yaml`:** switch model, NOS version, ASIC family, NIC model and
firmware, driver version, topology, MTU per tier, RDMA path MTU, ECMP hash fields and seed, BFD and
BGP timers, failure injected, number of runs, and per-run convergence (ms). Label results
`[MEASURED]` only with that manifest attached.

## 9. Intentionally flawed inputs

The intent dataset contains planted errors and legal-but-unusual configurations that test for false
positives. They are documented for instructors in `solutions/exercises-key.md` (Lab section), not
here.
