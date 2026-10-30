# Chapter 8 — Exercises Answer Key (INSTRUCTOR ONLY)

Marking conventions: full marks require the "evidence required" items in `exercises.md`. Deduct for
unlabelled numbers (–10 % of the item), arithmetic without the formula (–20 %), and any invented
command flag (–25 %; it would mislead a practitioner). All numbers below are `[MODELED]` unless marked.

---

## 8.1 Keys and access rights

- `lkey`: authorises the **local** NIC to read/write the registered buffer when it appears in a
  scatter/gather entry of a locally posted work request. `rkey`: handed to the **peer**; authorises the
  peer's RDMA READ/WRITE/atomic to target the buffer, within the MR's access flags.
- The MR lacks `IBV_ACCESS_REMOTE_WRITE`. The **target NIC** rejects the WRITE when it validates the
  `rkey` and access rights and returns a NAK (remote access error). Nothing is written. The
  **initiator** receives a CQE with status `IBV_WC_REM_ACCESS_ERR` (10) and its QP transitions to
  **ERROR**; all subsequent posted WRs flush with `IBV_WC_WR_FLUSH_ERR`. (The target application sees
  nothing for a WRITE; the target QP may also be moved to an error state depending on implementation.)

*Marking:* 2 pts definitions, 2 pts where checked/reported, 1 pt QP state. *Common mistake:* saying the
target application gets an error CQE.

## 8.2 Silent arrival

A WRITE is one-sided: the target NIC places data directly using the `rkey`, without consuming a RECV
WQE, so there is no work request at the target to complete. Notification options:

1. **Poll a flag/sequence word** written last (in the same or a following WRITE). Cost: burns a CPU
   core polling; must rely on in-order placement guarantees within the QP (write the flag after the
   data, ideally as a separate WRITE).
2. **Follow with a SEND** (or use **WRITE-with-immediate**), which consumes a posted RECV and produces a
   target CQE. Cost: the target must keep RECVs posted (RNR risk if it does not) and handle a completion
   per message; slightly more latency and CPU.

NCCL uses small control messages/flags in registered memory to signal readiness and completion.

## 8.3 Where the parameters live

(a) **INIT→RTR** sets path MTU, destination QPN, destination GID/LID and source GID index (address
vector), receive PSN, `max_dest_rd_atomic`, min RNR timer. (b) **RTR→RTS** sets `timeout`,
`retry_cnt`, `rnr_retry`, send PSN, `max_rd_atomic`.
Implication: a QP can reach RTS and pass small tests with a wrong path MTU or a marginal timeout; the
failure appears only when large packets (MTU) or transient stalls (timeout) occur — so check these
values (e.g., perftest's printed `Mtu` and `GID index` lines) rather than "it connected".

## 8.4 v1 versus v2

RoCEv1 is an Ethernet frame with EtherType **0x8915** carrying a GRH + BTH directly — no IP header.
ORION's backend is routed: every host NIC is on its own /31 to the leaf, and the leaf forwards by IP
routing. A v1 frame is addressed to the next hop's MAC (the leaf) but carries no IP header, so the
leaf cannot route it and drops it. Signatures: leaf ingress drops of non-IP/unknown-EtherType
frames rising on the host's port and zero RoCE (UDP 4791, DSCP 26 → TC3) packets from that port; on
hosts, `local_ack_timeout_err` rising on both peers, NCCL `error 12` (`IBV_WC_RETRY_EXC_ERR`), and no
`out_of_sequence` (nothing arrives at all, so no gaps).

## 8.5 Entropy

The UDP source port is the per-flow entropy field: switches hash the 5-tuple for ECMP, and the NIC
typically uses one source port per QP, so a QP stays on one path (no reordering) and different QPs
spread across paths. With two QPs per NIC pair, many elephant flows share few hash inputs; two heavy
QPs can land on the same spine uplink while another uplink idles — throughput for those flows halves,
and which flows collide changes run to run (different QPNs → different source ports), producing
bimodal or noisy bandwidth. Mitigations: (1) more QPs per connection (NCCL setting; more NIC state and
memory, but better statistical spreading); (2) rail-local placement so most traffic never crosses the
spine (Chapter 7 rail-optimized design; depends on scheduler/rank mapping); (3) adaptive routing or
packet spraying with selective-repeat-capable NICs (vendor-specific, needs reorder tolerance). Any two
with a trade-off earn full marks.

## 8.6 Reading `ibstat`

- `Initializing / LinkUp / Base lid 0`: the physical link trained; the **subnet manager** has not
  configured/activated the port (SM down, SM not sweeping this port, partition or SM issue). First
  command: `sminfo` (is there a master SM, which LID) — or check the SM's log; `ibstat` on a working
  port to compare `SM lid`.
- `Down / Polling`: no link partner — **cable, transceiver, or the remote (switch) port**. First
  command: `ibstat`/`iblinkinfo` from the switch side or `ibnetdiscover` to see the far end, then
  physical inspection (Chapter 10). `mlxlink` is vendor-specific and acceptable if labelled as such.

## 8.7 Lossless two ways

- **IB credit-based FC:** the receiver advertises free buffer per VL (64-byte blocks); the sender
  transmits only with credits. A packet is never sent without guaranteed buffer, so no overflow and no
  need to stop a sender "in time".
- **PFC (802.1Qbb):** the receiver sends a pause for a priority when its ingress buffer crosses a
  threshold (XOFF). Data already in flight on the cable and in the sender's pipeline still arrives
  after the pause is sent, so the receiver must reserve **headroom** ≈ (2 × cable propagation + response
  times) × link rate + MTU-sized terms (Chapter 9 gives the formula). Credits avoid this because the
  sender never transmits beyond what was granted.
- Back-pressure counters: IB `PortXmitWait` (perfquery); Ethernet per-priority pause counters on the
  NIC (`ethtool -S`, e.g. `rx_prio3_pause`/`tx_prio3_pause` on mlx5 — vendor names) and the switch's PFC
  tx/rx counters per priority.

## 8.8 Wire efficiency and marking

Per-packet overhead (untagged IPv4): preamble+SFD 8 + Ethernet 14 + IPv4 20 + UDP 8 + BTH 12 + ICRC 4
+ FCS 4 + IFG 12 = **82 B**.

(a) VLAN adds 4 B → 86 B. Efficiency = 2,048 / (2,048 + 86) = 2,048 / 2,134 = 0.9597.
Ceiling = 400 Gb/s × 0.9597 = **383.9 Gb/s**.

(b) IPv6 header is 40 B (20 B more) → 102 B. Efficiency = 4,096 / 4,198 = 0.9757.
Ceiling = 400 × 0.9757 = **390.3 Gb/s**.

(c) Packet rate = 400 × 10⁹ / (4,198 × 8) = 400 × 10⁹ / 33,584 = **11.91 M packets/s**.

(d) `NCCL_IB_TC` sets the whole traffic-class byte. 26 = 0b0001 1010. DSCP = top 6 bits =
0b000110 = **6**; ECN = bottom 2 bits = 0b10 = **ECT(0)**. DSCP 6 is not mapped by ORION's QoS policy
(only 26 → TC3 and 48 → TC6), so the traffic lands in the **default lossy class** — no PFC protection;
it is ECN-capable, but whether that queue has an ECN profile is switch-policy-dependent. Correct value:
26 × 4 + 2 = 106.

*Common mistakes:* forgetting preamble/IFG (gives 98.5 % at 4,096 — "frame efficiency", not wire
efficiency); treating `NCCL_IB_TC` as a DSCP value.

## 8.9 The price of a lost packet

(a) Packets = 1,048,576 / 4,096 = **256**. Time = 1,048,576 × 8 / 392 × 10⁹ = 8,388,608 / 392 × 10⁹ =
**21.4 µs**.

(b) BDP = 49.0 GB/s × 5 µs = 245,000 B ≈ 245,000 / 4,096 = **60 packets**. Under go-back-N the NAK for
packet 50 arrives about one RTT after packet 50 was sent; meanwhile packets 51…≈110 were sent and are
discarded. Extra time ≈ wasted transmission ≈ 60 × 4,096 × 8 / 392 × 10⁹ = **5.0 µs ≈ one RTT**,
≈ 23 % of 21.4 µs. (Accept 5–10 µs if the student adds NAK processing time and states it.)

(c) T_ack = 4.096 µs × 2¹⁸ = 4.096 µs × 262,144 = **1.074 s** extra — ≈ 50,000× the transfer time.

(d) For *isolated* messages (QP idle after each), only a lost final packet (or final ACK) forces a
timeout. P ≈ p = 10⁻⁵ per message. Expected timeout cost per message = 10⁻⁵ × 1.074 s = **10.7 µs**.
Mid-message losses: 256 × 10⁻⁵ = 0.00256 per message × 5 µs = 0.013 µs (negligible). Goodput ≈
21.4 / (21.4 + 10.7 + 0.013) ≈ **0.67 → ≈ 67 %**. For **back-to-back** messages the next message's
first packet reveals a lost tail and triggers a NAK, so the timeout exposure is per *burst* (the last
packet before the QP idles): with bursts of *k* messages the timeout cost is amortised over *k*
messages (≈ 10.7 / *k* µs each). Lesson: with long timeouts, even a 10⁻⁵ loss rate can cost a third
of throughput for idle-between-messages traffic; the fabric must be effectively loss-free or the NIC
must recover tail loss faster (selective repeat, `[VENDOR-SPEC, 2026-10]`).
*Common mistake:* applying p × T_ack to every message of a continuous stream.

(e) (retry_cnt + 1) × T_ack = 8 × 1.074 s = **8.59 s**.

*Marking:* 2 pts each part. *Common mistake:* charging the whole remainder of the message (packets
50–256) as waste in (b); only packets sent after the loss before the NAK arrives are wasted.

## 8.10 Draw the two data paths

Expected diagrams match Manuscript Figures 8.1 and 8.2. Count table (per message; 1 MiB is many TCP
segments but copies are per byte, so count copy *passes*):

| | TCP sender | TCP receiver | RDMA WRITE initiator | RDMA WRITE target |
|---|---|---|---|---|
| CPU copies | 1 (user→socket buffers) | 1 (socket buffers→user) | 0 | 0 |
| DMA | 1 (NIC reads skbs) | 1 (NIC writes ring) | 1 (NIC reads MR) | 1 (NIC writes MR) |
| System calls | ≥ 1 `send()` (may be several for 1 MiB) | ≥ 1 `recv()`/`epoll_wait()` | 0 | 0 |
| Interrupts | TX completion IRQs (moderated) | RX IRQs (moderated, NAPI) | 0 if polled (1 if CQ armed for events) | 0 |
| Context switches | 0–1 (blocking send when buffer full) | 0–1 (wake blocked receiver) | 0 | 0 |
| Kernel involvement | TCP/IP, buffers | TCP/IP, ACKs | none on data path | none |
| Remote CPU | — | yes | — | no |

Offloads: TSO/GSO and checksum offload reduce per-segment CPU work; GRO/LRO and interrupt moderation
cut interrupts; `MSG_ZEROCOPY` removes the *send-side* copy for large sends (with completion
notifications). None removes the receive-side copy for ordinary sockets or kernel TCP processing.
(Kernel TCP receive zero-copy via `mmap`/`TCP_ZEROCOPY_RECEIVE` exists but needs page-aligned
payloads and specific NIC support — credit a student who mentions it with that caveat.)

*Marking:* 4 pts diagrams, 4 pts table, 2 pts offloads.

## 8.11 RoCEv2 versus InfiniBand design note (deliverable)

A model answer contains:

- **Comparison** along the four mandated dimensions (Manuscript Table 8.5): transport (UDP/IP
  port 4791 vs native LRH/BTH), management (distributed BGP + per-switch QoS automation vs subnet
  manager), operations (Ethernet skills/multi-vendor vs specialist/single-vendor), evidence (switch
  queue/ECN/PFC + NIC hw counters vs `perfquery`/`PortXmitWait`/SM logs).
- **Recommendation** for Halcyon (either is acceptable if criteria-driven). A typical RoCEv2 answer:
  Halcyon already runs a large Ethernet estate and the Fabric team automates switch config; RoCEv2
  lossless (PFC prio 3 + ECN/DCQCN) because ORION NICs are assumed go-back-N; accept configuration risk
  and mitigate it with the readiness validator and switch config compliance checks.
- **Addressing/GID:** `10.100.r.(2n+1)/31` per rail, per-rail policy routing; GID chosen as the RoCE v2
  entry matching the rail IP (validated per host) or rdma_cm.
- **QoS:** DSCP 26 → TC3 (PFC + ECN), CNP DSCP 48 → TC6 strict; `NCCL_IB_TC = 26 × 4 + 2 = 106`.
- **MTU:** host 9000, RDMA 4096, switch 9216 (with the "4,158-byte frame fits" arithmetic).
- **Timeout:** e.g. `timeout` 18–20, `retry_cnt` 7 → 8.6–34 s to failure, justified by tolerance of
  PFC transients versus slow detection; mention that NCCL's defaults are version-specific.
- **Multi-rail failure:** one rail lost = –12.5 % node bandwidth; synchronous job runs at the degraded
  node's pace; policy: drain and replace rather than run degraded for long jobs.
- **Failure signatures:** mis-marked traffic in lossy queue; PFC storm/pause propagation (Ch 9);
  switch-port MTU mismatch / GID index; optics/FEC degradation (Ch 10).

*Marking (20):* comparison 6, recommendation with criteria 4, numbers with labels 5, failure
signatures 3, cross-references 2. *Common mistakes:* claiming IB "never congests" (it back-pressures);
claiming RoCEv2 requires PFC (it does not; lossless is a design choice tied to NIC recovery).

## 8.12 Pre-deployment readiness checklist (deliverable)

Model answer = Manuscript Table 8.10 plus three columns. Key grading points:

| # | Item | Read-only | Automated in lab |
|---|---|---|---|
| 1–2 | Devices present/mapped; port state | yes | yes (PORT_STATE) |
| 3 | Link layer, speed | yes | yes (LINK_LAYER, LINK_SPEED) |
| 4–5 | Firmware, driver vs matrix | yes | yes (FIRMWARE, DRIVER) |
| 6 | Netdev MTU + `active_mtu` | yes | yes (MTU) |
| 7 | Address plan | yes | yes (ADDRESS_PLAN) |
| 8 | GID index → RoCE v2 + rail IP | yes | yes (GID_INDEX) |
| 9–10 | DSCP trust + map, PFC priorities | yes | map and PFC yes (QOS_DSCP, QOS_PFC); trust mode no |
| 11 | `NCCL_IB_TC=106` | yes | no (good extension) |
| 12 | Peer-memory/DMA-BUF mechanism present (necessary, not sufficient) | yes | yes (PEERMEM) |
| 13 | PCIe LnkSta = LnkCap | yes | correlation only (perftest part) |
| 14 | NUMA locality | yes | no |
| 15 | ACS/IOMMU allow GPU↔NIC peer-to-peer (`lspci -vvv` ACSCtl) | yes | no |
| 16 | Locked-memory limit `unlimited` (shell, Slurm job, container) | yes | no |
| 17 | Per-rail policy routing and neighbour resolution (`ip rule`, `ip neigh`) | yes | no |
| 18 | **Switch side**: port speed, MTU 9216, trust/DSCP→TC, PFC, ECN profile | yes (read config/telemetry) | no — needs switch API/CLI or config-compliance tooling |
| 19 | Peer validation: pingpong `-m 4096`, perftest per rail, `ib_write_bw --use_cuda` per rail | **no** (loads the fabric; drained nodes only) | analysis only |
| 20 | Error-counter baseline | yes | no |

Lab coverage (same wording everywhere): the lab automates items 1–10 (item 9: DSCP map only) and 12 and correlates item 13 with perftest results.

Items not verifiable from host captures: switch-port MTU and QoS (item 18), whether GPUDirect RDMA
actually works (only item 19's `--use_cuda` run proves it; item 12 alone does not), cabling to the right
leaf port (LLDP neighbour data from host `lldpctl` or switch tables), and fabric-wide behaviour under
load. Ordering rationale: cheap read-only checks first; peer validation only after config is right
(otherwise you benchmark a misconfiguration and may disturb neighbours).

*Marking (20):* coverage of outline categories (NIC, firmware, driver, addressing, MTU, peer
validation) 8; criteria precise and testable 6; read-only/automation flags 3; switch-side gap 3.

## 8.13 Lab

Reference implementation: `solutions/lab/readiness.py`, `solutions/lab/perftest_analysis.py`;
`python lab/check.py --impl solution` → 15/15 PASS (14/14 + 1 SKIP in the student release, where `lab/tools/` is stripped). Planted faults and expected diagnoses:
[`lab/PLANTED_FAULTS.md`](lab/PLANTED_FAULTS.md). Reference report summary:

```text
Nodes checked: 8; ready: 2; findings: 16
orion-n01 READY | n02 FIRMWARE | n03 LINK_SPEED, PORT_STATE | n04 QOS_PFC
n05 GID_INDEX (all 8 devices) | n06 MTU (mlx5_3), PEERMEM | n07 ADDRESS_PLAN (mlx5_2, mlx5_3) | n08 READY
perftest: n05-n06 rail 5 BW flag (plateau 202.4 Gb/s vs fleet median 388.6) -> orion-n05 mlx5_5 PCIe x8
          n07-n08 rail 2 TAIL flag (p99.9 29.2 us vs fleet median 3.44 us)
```

Diagnosis grading (20 pts in the lab rubric): BW pair — PCIe x8 identified with arithmetic (Gen5 x8 ≈
252 Gb/s raw, ≈ 200–215 Gb/s achievable ⇒ ≈ 202 Gb/s plateau), small-message rate unchanged (not a NIC
pipeline issue), next test (cold-boot LnkSta, AER in `dmesg`, reseat/swap slot). TAIL pair — typical
latency normal so not path/MTU; hypotheses host jitter vs PFC pauses vs marginal link; next tests named;
explicit statement that `[SIMULATED]` data cannot discriminate.

## 8.14 L3 extension

No fixed answer. Check: manifest complete; ≥ 5 runs; warm-up discarded; NUMA pinning stated; median
and spread reported; model comparison uses the student's actual link speed and MTU (e.g., 200 Gb/s:
ceiling 196 Gb/s at 4,096 MTU; 100 Gb/s: 98.0 Gb/s). A measured plateau 1–3 % below the wire ceiling is
normal; > 5 % below needs an explanation (PCIe, NUMA, MTU, CPU frequency, competing traffic).

## 8.15 Small messages work, large ones do not

(a) Ranked hypotheses: (1) **MTU mismatch on the new leaf's ports to `rack-04`** — a port left at 1,500
(template default) drops frames larger than 1,500 B; fits "≤ 1,024 works, larger fails", the
oversize-drop counter, and the rack-scoped impact. (2) QoS/PFC misconfiguration on those ports —
would cause loss under load but not a hard size threshold, and would not increment oversize drops.
(3) Faulty optics/cables — ruled down by zero FEC-uncorrectable/CRC and the clean size threshold.
(Host MTU is ruled out by evidence: 9000 and `active_mtu` 4096 on both.)

(b) Discriminating tests (drained nodes; read-only or low-volume):
- `ping -M do -s 8972 -c 3 10.100.6.26` (n13's leaf-side address, 10.100.6.(2×13)) — DF-set 9,000-byte
  IP packet to the leaf fails if the leaf interface MTU is 1,500; `-s 1472` succeeds.
- `ib_write_bw -d mlx5_6 -x 3 -a -F --report_gbits -m 1024 10.100.6.29` — forcing a 1,024-byte path
  MTU, the full sweep completes at ≈ 370 Gb/s plateau (Table 8.4), while the default (4,096) stalls.
- Read (do not change) the leaf port configuration with the Fabric team.

(c) Root cause: the replacement leaf's ports toward `rack-04` carry the default 1,500-byte MTU. Packet-size
arithmetic (RoCEv2 IP packet = 20 IP + 8 UDP + 12 BTH + [16 RETH on a first/only packet] + payload +
4 ICRC): a 1,024-byte "only" packet → 1,084 B ≤ 1,500 passes; a 2,048-byte message as one packet →
2,108 B > 1,500 dropped; any message > 1,024 B is sent in packets of up to 4,096 B → dropped. Hence
the perftest sweep stops after the 1,024 row. `ibv_rc_pingpong` passes because its **default path MTU
is 1,024** (`-m` option), so its 4,096-byte messages travel as four 1,024-byte packets — a trap that
makes a "connectivity test" look healthy. The drops are tail-of-message and every-packet losses, so
the initiator never gets ACKs → `IBV_WC_RETRY_EXC_ERR`.

(d) Fix: Fabric team corrects the port MTU to 9,216 (per ORION standard) through change control,
compares the whole replacement leaf's config against the golden template, and adds an MTU compliance
check to the switch-replacement runbook. Validation: DF ping at 8,972 B passes from each `rack-04` node to
the leaf; `ib_write_bw -a` per `rack-04` node on rail 6 reaches ≈ 390 Gb/s; an NCCL job including `rack-04`
completes with bus bandwidth in the normal band; oversize-drop counter stops increasing.

*Marking (20):* hypotheses 5, tests 5 (–2 for any non-existent flag), arithmetic/mechanism 6, fix +
validation 4. *Common mistakes:* blaming host MTU despite evidence; changing switch MTU directly from
the host incident without the Fabric team; not explaining the pingpong pass.

## 8.16 ORION-XL fabric policy

Open-ended; grade on reasoning. A strong answer, for example: RoCEv2, lossless on the RoCE class with
ECN/DCQCN tuned first (PFC as a safety net), unless the selected NIC generation's selective repeat is
validated at L3, in which case a lossy-RoCE pilot on one pod. 3-tier RTT stated, e.g. ≈ 8–10 µs
`[ILLUSTRATIVE]` → BDP at 400 Gb/s ≈ 49 GB/s × 10 µs = 490 KB ≈ 120 packets; `timeout` 20 (4.29 s) and
`retry_cnt` 7 → 34 s to failure accepted because a spurious failure costs a 4,096-GPU restart, and
quantified tail-loss cost at the design loss rate (e.g. 10⁻⁷: 10⁻⁷ × 4.29 s = 0.43 µs per message —
acceptable for MiB-scale messages). MTU 4,096 everywhere with automated switch compliance. GID via
validated per-host derivation. Checklist at 512 nodes: fully automated in the admission pipeline, 100 %
of nodes on every change (no sampling for config), peer perftest against a rotating reference node per
rail. Single-NIC failure mid-job: NCCL error → job restarts from checkpoint excluding the node
(Chapter 19); do not run degraded. Accepted risk example: PFC storms — detected by pause-duration
counters and PFC watchdog alerts (Chapter 9). An InfiniBand answer is equally valid if it covers SM
scale (sweep time, redundancy), partitioning, and adaptive routing dependencies.

*Marking (20):* decision + criteria 5, parameters with numbers 6, quantified trade-off 4, accepted
risk + detection 3, scale considerations 2.

## 8.17–8.20 Reflection

**8.17** Any three: congestion and incast across many senders (PFC/ECN behaviour, Chapter 9); ECMP or
rail collisions with many flows; GPUDirect RDMA path (host-memory test bypasses GPU↔NIC PCIe P2P);
NCCL algorithm/protocol overheads and synchronisation; stragglers from other nodes; long-run stability
(link flaps, FEC degradation).

**8.18** Examples: switch-side misconfiguration (MTU, trust, PFC) invisible to host captures → switch
config compliance/telemetry; GPUDirect RDMA mechanism loaded but P2P blocked by ACS/IOMMU → GPU-buffer
perftest (`--use_cuda`) or NCCL test (Chapter 13); firmware matches baseline but the baseline itself is
outside the vendor matrix for this driver → matrix check; cabled to the wrong leaf port while addresses
are right → LLDP neighbour check; `NCCL_IB_TC` not checked by the lab.

**8.19** In `[MEASURED]` data with a manifest, "pair X on rail Y has a plateau of 202 Gb/s and a PCIe
link at x8" becomes an observed fact; the *causal* claim that x8 caused the shortfall becomes strongly
supported (modelled ceiling matches) but is proven only by a fix-and-retest (reseat → x16 → plateau
recovers). The tail-latency cause remains a hypothesis until a discriminating test (pinning, different
peer, pause counters in the run window) separates host jitter from fabric pauses. In `[SIMULATED]` data
none of these are facts about hardware.

**8.20** Correlation-only: "the config push happened at 14:05 and failures began at 14:10" or "only
n05 changed". Missing causal link: a mechanism (GID index 2 = RoCEv1 → non-routable → no ACKs) plus a
test that changes only the suspected variable (`-x 3` passes, `-x 2` fails) and leaf counters
consistent with the mechanism.

---

## Regenerating checker hashes

If you change the generator or seed, regenerate data and recompute the hashes stored in `lab/check.py`:

```bash
cd solutions/lab
python -c "import hashlib,readiness as r,perftest_analysis as p;from pathlib import Path;d=Path('../../lab/data');h=lambda s:hashlib.sha256(('ch08:'+s).encode()).hexdigest()[:16];f,v=r.run_readiness(d/'inventory',d/'baseline.yaml');print(sorted(h(x.key) for x in f));print(sorted(h(k+'|'+x) for k,x in v.items()));df=p.summarize(d/'perftest');print([h(f'{a.pair}|{a.rail}|BW') for a in df.itertuples() if a.bw_flag],[h(f'{a.pair}|{a.rail}|TAIL') for a in df.itertuples() if a.tail_flag])"
```
