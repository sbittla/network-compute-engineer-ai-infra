# Chapter 8 — Exercises

Difficulty: ★ foundational · ★★ intermediate · ★★★ advanced. Tier: L1 laptop/simulation · L2 single
GPU host · L3 multi-node with RDMA. Every exercise states the evidence required for full marks. Use the
ORION values in [docs/REFERENCE_CLUSTER.md](../../../docs/REFERENCE_CLUSTER.md) unless an exercise
changes them, and label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]`, or `[ILLUSTRATIVE]`.

**Chapter deliverable (course outline):** *RDMA design note and deployment-readiness checklist* —
Exercises 8.11 and 8.12, supported by the lab report (Exercise 8.13).

---

## Knowledge checks

**8.1 Keys and access rights** ★ · L1
Explain the difference between an `lkey` and an `rkey`. An initiator posts an RDMA WRITE to a remote
buffer whose MR was registered with only `IBV_ACCESS_LOCAL_WRITE | IBV_ACCESS_REMOTE_READ`. What
happens, where is it reported, and what state does the initiator's QP end up in?
*Evidence required:* correct definitions; the failing check and the completion status; resulting QP
state.

**8.2 Silent arrival** ★ · L1
Why does an RDMA WRITE produce no completion at the target? Give two ways the target application can
learn that the data has arrived, and one cost of each.
*Evidence required:* mechanism stated; two notification methods with a cost each.

**8.3 Where the parameters live** ★ · L1
At which queue-pair state transition are (a) the path MTU and destination GID/GID index, and (b) the
ACK timeout and retry count set? Why does that matter when you troubleshoot a QP that connects but
fails under load?
*Evidence required:* transitions named correctly; one-sentence troubleshooting implication.

**8.4 v1 versus v2** ★ · L1
Explain why a RoCEv1 GID cannot work on ORION's backend, and what an operator would see in counters
on the leaf and on the hosts.
*Evidence required:* encapsulation difference (EtherType vs UDP/IP); routed /31 consequence; at least
two counter-level signatures.

**8.5 Entropy** ★★ · L1
What role does the UDP source port play in RoCEv2? A rail-to-rail all-to-all uses two QPs per NIC pair.
Explain why bandwidth may vary between otherwise identical runs, and two mitigations.
*Evidence required:* ECMP hashing mechanism; collision explanation; two mitigations with their
trade-off.

**8.6 Reading `ibstat`** ★ · L1
An InfiniBand port shows `State: Initializing`, `Physical state: LinkUp`, `Base lid: 0`. Another shows
`State: Down`, `Physical state: Polling`. For each, name the most likely failing component and the
first command you would run.
*Evidence required:* correct component for each; a real command for each.

**8.7 Lossless two ways** ★★ · L1
Compare InfiniBand credit-based flow control with Ethernet PFC: how each prevents buffer overflow,
why one needs headroom buffer and the other does not, and which counter shows back-pressure on each.
*Evidence required:* mechanism of each; headroom reasoning; `PortXmitWait` and per-priority pause
counters named.

## Worked problems

**8.8 Wire efficiency and marking** ★★ · L1
(a) Compute the payload ceiling of a 400 Gb/s RoCEv2 link at a 2,048-byte path MTU when a VLAN tag is
present (IPv4). (b) Compute it at 4,096 bytes over IPv6, untagged. (c) Compute the packet rate at line
rate for case (b). (d) A host is configured with `NCCL_IB_TC=26`. What DSCP and ECN codepoint do its
RoCE packets carry, and in which ORION queue do they land?
*Evidence required:* overhead per packet itemised; formula → substitution → result with units for
each part; DSCP/ECN bit arithmetic shown.

**8.9 The price of a lost packet** ★★★ · L1
A 1 MiB RDMA WRITE goes from GPU 2 on one ORION node to GPU 5 on another — different rails, so it
crosses a spine (path MTU 4,096; payload ceiling 392 Gb/s; cross-rail round-trip time 5 µs
`[ILLUSTRATIVE]`, docs/REFERENCE_CLUSTER.md). (a) How many packets is the message, and how long
does it take without loss? (b) Under go-back-N, estimate the extra time if packet 50 is lost.
(c) Estimate the extra time if the last packet is lost and `timeout` = 18. (d) With independent
per-packet loss probability 10⁻⁵, estimate the expected goodput of a series of such *isolated*
messages (the QP idles after each) from tail-loss timeouts alone, and say how the answer changes for
back-to-back messages. (e) How long until a QP with `timeout` = 18 and `retry_cnt` = 7 reports
`IBV_WC_RETRY_EXC_ERR` if the peer dies?
*Evidence required:* every step as formula → values → result; bandwidth-delay product computed;
assumptions stated; labelled `[MODELED]`.

## Outline-mandated exercises

**8.10 Draw the two data paths** ★ · L1 *(course outline, Chapter 8 exercise 1)*
Draw the data path for a 1 MiB message sent with TCP sockets and with an RDMA WRITE between two
ORION nodes. For each side, count CPU copies, DMA transfers, system calls, interrupts, and context
switches, and mark where the kernel and the remote CPU are involved. State which offloads would change
your counts and which counts they cannot remove.
*Evidence required:* two labelled diagrams (Mermaid or hand-drawn); a count table per side; offload
discussion.

**8.11 RoCEv2 versus InfiniBand design note** ★★ · L1 *(course outline, Chapter 8 exercise 2; part of the
chapter deliverable)*
Write a one- to two-page RDMA design note for ORION's backend that compares RoCEv2 and InfiniBand
across **transport, fabric management, operational model, and troubleshooting evidence**, and makes a
recommendation for Halcyon AI. Include: addressing and GID policy, QoS marking (DSCP/TC values with
arithmetic), MTU policy at all three layers, ACK timeout/retry choice with its time-to-failure,
multi-rail failure behaviour, and the three most likely failure signatures for your choice.
*Evidence required:* comparison table with all four dimensions; recommendation tied to stated
criteria; every number labelled; at least one cross-reference to Chapter 9 (congestion) and Chapter 10
(physical layer).

**8.12 Pre-deployment readiness checklist** ★★ · L1 *(course outline, Chapter 8 exercise 3; part of the
chapter deliverable)*
Create a pre-deployment checklist for an RDMA-capable cluster covering **NIC, firmware, driver,
addressing, MTU, and peer validation** (plus QoS and GPUDirect RDMA). For each item give the command or
data source, the pass criterion, whether it is read-only, and whether your lab validator automates it.
Identify the items that cannot be verified from host captures alone and say how you would get that
evidence.
*Evidence required:* ≥ 15 items with command, criterion, read-only flag, automation flag; switch-side
items identified with an evidence source; ordering justified.

## Hands-on lab

**8.13 RDMA readiness validator and perftest analyzer** ★★ · L1
Complete [lab/README.md](lab/README.md) Tasks 1–8. Submit `readiness_report.md`, `diagnosis.md`, and
your completed starter modules.
*Evidence required:* `python check.py` output showing all checks PASS; the report; a diagnosis for each
flagged perftest pair with mechanism, evidence, and next discriminating test, stating that the data are
`[SIMULATED]`.

**8.14 L3 extension: measure a rail** ★★★ · L3
On a dedicated lab fabric, collect real inventories from two nodes, run your validator, then run
`ib_write_bw -a` and `ib_write_lat -a` on at least two rails (five repetitions each, warm-up discarded,
NUMA-pinned). Compare the measured plateau and n½ with the Section 8.11 model for your link speed and
MTU.
*Evidence required:* raw captures; filled-in `manifest.yaml` with `evidence_class: MEASURED`; median
and min/max for plateau and p99/p99.9; model-versus-measured table with an explanation of any gap.

## Troubleshooting case

**8.15 Small messages work, large ones do not** ★★★ · L1 (tabletop) / L3 (reproduce in a lab)
After the rail-6 leaf was replaced over the weekend (its configuration restored from a template), NCCL
jobs that include any `rack-04` node (`orion-n13`…`orion-n16`) hang during the first large all-reduce and
later fail with `IBV_WC_RETRY_EXC_ERR`; jobs without `rack-04` nodes are healthy. Evidence collected so far
`[ILLUSTRATIVE]`:

- `ibv_devinfo` on `orion-n13` and `orion-n14`: `mlx5_6` `PORT_ACTIVE`, `active_mtu 4096 (5)`.
- `ip -o link`: `ens7np0 … mtu 9000` on both nodes.
- `ib_write_bw -d mlx5_6 -x 3 -a -F --report_gbits 10.100.6.29` from n13 to n14 prints rows up to
  `#bytes 1024` normally, then stops producing output; after several seconds the client exits with a
  completion error.
- `ibv_rc_pingpong -d mlx5_6 -g 3 10.100.6.29` (default options) completes normally.
- `orion-be-leaf-r6`, ports to n13 and n14: link up at 400G, zero FEC uncorrectable and CRC errors; an
  "oversize/giant frames dropped" counter (vendor name varies) is non-zero and rising.

(a) Rank three hypotheses. (b) Propose two discriminating tests that are safe to run, with exact
commands. (c) State the most likely root cause and the mechanism by which it produces *exactly* this
pattern (which message sizes pass and why). (d) Describe the safe fix and the validation.
*Evidence required:* hypotheses ranked with reasons; real commands; packet-size arithmetic showing
which sizes fit; fix routed through the Fabric team with change control; validation criteria.

## Design challenge

**8.16 ORION-XL fabric policy** ★★★ · L1
Halcyon is building ORION-XL (512 HX8 nodes, 4,096 GPUs, 3-tier Clos; docs/REFERENCE_CLUSTER.md §4).
Choose RoCEv2 or InfiniBand for its backend and specify, with justification: the loss model (lossless
vs lossy, and the NIC capability you depend on), ACK timeout and retry values (with time-to-failure),
path MTU, GID/addressing policy, how the readiness checklist changes at 512 nodes (automation,
sampling, admission gates), and what you would do when a single NIC fails mid-job. Use numbers:
bandwidth-delay product for a 3-tier round trip you state, and the expected cost of tail loss at the
loss rate you design for.
*Evidence required:* decision with criteria; every parameter with its number and label; one
quantified trade-off; one risk you are accepting and how you would detect it in production.

## Reflection and review

**8.17** ★ · L1 — Name three things a two-node `ib_write_bw` result at 390 Gb/s does **not** tell you about
a 256-GPU training job on the same fabric. *Evidence required:* three distinct gaps, each tied to a
mechanism (e.g., congestion, rail collisions, GPUDirect path).

**8.18** ★ · L1 — Your validator reports `orion-n01` READY. List three ways that verdict could still be
wrong (false negatives), and which additional evidence would close each gap. *Evidence required:* three
gaps with an evidence source each.

**8.19** ★★ · L1 — The lab's perftest data are `[SIMULATED]`. Which conclusions in your `diagnosis.md`
would change status if the same patterns appeared in `[MEASURED]` data with a manifest, and which
would still be hypotheses? *Evidence required:* explicit classification of each conclusion.

**8.20** ★★ · L1 — The GID-index scenario in Section 8.13 was caught by a discriminating test. Describe
what evidence would have been merely *correlation* and why it would not have justified the change on
its own. *Evidence required:* one correlation-only signal and the missing causal link.
