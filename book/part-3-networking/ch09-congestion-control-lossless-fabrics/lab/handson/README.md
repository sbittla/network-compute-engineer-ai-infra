# Chapter 9 hands-on lab: ECN and incast with `tc`

## 1. What you will do

You build a one-switch fabric on one Linux machine: up to 16 sender namespaces, a receiver and a probe,
joined by a Linux bridge in a "switch" namespace. The switch port that faces the receiver is the
bottleneck: a token bucket drains it at 100 Mbit/s, and a `tc` qdisc you choose is its egress queue. You
run a synchronized 8:1 TCP incast with iperf3 into that queue five ways: drop-tail, RED with ECN marking
using the chapter's template thresholds, the same RED queue with senders that do not negotiate ECN, the
as-found thresholds of Section 9.10, and DCTCP. For each one you measure what the chapter tells an
operator to read: marks, drops, queue depth and queueing delay, goodput and fairness.

## 2. What is real here, and what is not

Real: the Linux kernel's TCP stacks (cubic and DCTCP) negotiating ECN in the SYN handshake, ECT(0) in
the IP header of every data packet, a real RED queue (`sch_red`) computing an average queue length and
marking CE or dropping by the Kmin/Kmax/Pmax profile of Figure 9.2, real CE codepoints counted on arrival
by the receiver's IP stack (`IpExtInCEPkts`), ECN-Echo back to the senders, and senders that cut their
windows in response. The queue is a real egress queue with a real 500,000-byte limit, and every drop and
mark is counted by the kernel. Every number in the reference results is `[MEASURED]`.

The thresholds are the chapter's numbers scaled to this fabric. The bottleneck runs at 100 Mbit/s and
netem adds 2 ms to everything the receiver sends, so the base RTT is about 2 ms and the BDP about
25 KB. That is 1/8 of ORION's 200 KB same-rail BDP (Section 9.3), so every byte threshold is ORION's
divided by 8:

| | ORION (Sections 9.3, 9.7, 9.10) | This lab |
|---|---|---|
| Link rate, base RTT | 400 Gb/s, ≈ 4 µs | 100 Mbit/s, ≈ 2 ms |
| BDP | 200 KB | 25 KB |
| Hot-queue buffer share | 4 MB (20 BDP) | 500 KB (20 BDP) |
| Template Kmin / Kmax / Pmax | 150 KB / 1,500 KB / 20 % | 18,750 B / 187,500 B / 20 % |
| As found on `orion-be-leaf-r3` | 1,500 KB / 6,000 KB / 20 % | 187,500 B / 750,000 B / 20 % |

Not real, or not ORION:

- **TCP, not RoCE.** The senders are TCP flows, which back off on ECN-Echo and on loss and retransmit
  selectively. RoCEv2 NICs react to CNPs with DCQCN (Section 9.6) and recover from loss with go-back-N,
  which is far more expensive. DCTCP is the TCP algorithm closest to DCQCN in spirit, because it cuts
  its window in proportion to the fraction of marked packets.
- **No PFC.** A Linux bridge has no priority flow control, so this fabric is lossy: when the queue is
  full it drops. This is ORION's configuration C (Table 9.7), not the lossless class. There are no
  pause frames, headroom, HOL blocking or watchdog to measure.
- **Time scale.** Everything runs about a thousand times slower than ORION (milliseconds, not
  microseconds), and the queue's dynamics include the host's scheduler. The ratios hold: thresholds
  against BDP, and queueing delay against base RTT. The absolute values do not.
- **One queue, one switch.** There is no shared-buffer dynamic threshold, no multi-hop congestion tree
  and no ECMP. Linux RED marks on an exponentially weighted *average* queue, where many switch ASICs
  mark on the instantaneous depth.

The Level 3 extension in [../README.md](../README.md) (Section 9) runs the A/B threshold experiment of
Section 9.11 on a lab leaf with RDMA NICs, PFC and DCQCN; that is where pause duration, CNPs and the real
magnitude of the effect are measured.

## 3. Requirements

| Item | Need |
|---|---|
| GPU | No |
| Docker | No |
| Root | Yes: namespaces, veths, the bridge, `tc`, per-namespace sysctls |
| Kernel | veth, bridge, and the `tbf`, `red` and `netem` qdiscs; optionally `tcp_dctcp`. Stock Ubuntu and stock WSL2 kernels load them as modules on demand. A custom kernel built with `make bzImage` only has no modules: build them from the same tree (`make net/sched/sch_tbf.ko net/sched/sch_red.ko net/sched/sch_netem.ko net/bridge/bridge.ko net/802/stp.ko net/llc/llc.ko net/ipv4/tcp_dctcp.ko` after `make vmlinux`, then install and `depmod`), or rebuild with them set to `=y`. `setup.sh` tests each one in a throwaway namespace. |
| Packages | iperf3 3.16, ethtool, iproute2, iputils-ping (installed by `setup.sh`) |
| Disk, RAM | about 10 MB of results; under 300 MB of RAM |
| Time | setup under 1 min; run about 8 min |

## 4. Safety

- Everything lives in network namespaces named `ch09-*`: `ch09-sw` (the bridge `ch09-br`), `ch09-rx`,
  `ch09-pr` and `ch09-h1` to `ch09-h16`. The veth pairs are created directly inside those namespaces, so
  no lab interface ever appears in the host's namespace. The lab never touches `eth0` or any other real
  interface, route, sysctl or firewall rule. `tcp_ecn` and the congestion control are set per namespace.
- The qdiscs sit on `ch09-srx` and `ch09-rx0`, inside the lab's namespaces.
- `teardown.sh` kills every process in a `ch09-*` namespace, deletes the namespaces (which deletes their
  veths, the bridge and the qdiscs) and verifies that nothing is left. `run.sh` calls it on exit, also
  after a failure.
- The incast loads one or two CPUs. On a real network this experiment saturates links, so run it only on
  a lab fabric (Section 9.11).

## 5. Setup

```bash
cd book/part-3-networking/ch09-congestion-control-lossless-fabrics/lab/handson
sudo bash setup.sh          # iperf3, ethtool; tests veth, bridge, tbf, red (ecn), netem, bfifo, dctcp
sudo bash run.sh my-run     # the whole lab, unattended (about 8 min) -> results/my-run/
python3 check.py results/my-run
```

From the repository root on Windows: `python scripts/handson.py setup ch09`, `... run ch09 my-run`,
`... check ch09 my-run`.

To follow the steps by hand, build the fabric and keep it until you run `teardown.sh`:

```bash
sudo bash net.sh up 16              # 16 senders, probe, receiver, bridge, bottleneck (drop-tail)
sudo bash net.sh ecn 1              # tcp_ecn=1 in every sender namespace
sudo bash net.sh show               # addresses, bridge ports, qdiscs with counters
sudo bash net.sh queue red          # change the bottleneck's queue: droptail | red | asfound | dctcp
sudo bash incast.sh /tmp/x 8 15     # one 8:1 incast of 15 s with all its evidence in /tmp/x
```

`incast.sh` starts one iperf3 server per sender on the receiver, snapshots the queue's counters and the
receiver's `/proc/net/netstat`, samples the queue every 20 ms (`qsample.py`), pings the receiver every
20 ms from the probe through the same queue, and starts all N clients at once. The probe's pings carry
ECT(0) (`ping -Q 2`), so a RED queue marks them instead of dropping them, and they measure the queue
rather than its drop policy.

Why GSO, TSO and GRO are off on every veth (`net.sh` does it): with them on, the queue holds 64 KB
super-packets, RED counts one "packet" where the wire would carry 44, and the queue's depth jumps in
64 KB steps. Off, it holds 1,514-byte frames, as a switch does.

## 6. Steps

Write your answers in `results/<run-id>/answers.md`.

### Step 1: build the fabric and measure it

```bash
sudo bash net.sh up 16 && sudo bash net.sh show
sudo ip netns exec ch09-pr ping -D -n -i 0.02 -c 100 -Q 2 10.209.0.100      # idle RTT
sudo bash incast.sh /tmp/one 1 10                                          # one flow, drop-tail
```

Look for: the bottleneck's qdisc tree (`tbf rate 100Mbit` as root, the queue under test as its child
`10:`), the netem qdisc on `ch09-rx0`, and the offloads off. The idle RTT should be just over 2 ms. One
flow should get close to 95.6 Mbit/s: 100 Mbit/s × 1,448 / 1,514, because each 1,514-byte frame in the
queue carries 1,448 bytes of payload. Raw output: `step1-fabric/`.

**Question 1.** Compute this fabric's BDP from your idle RTT. How many full-size frames is it, and how
many BDPs of buffer does the 500,000-byte queue hold? Which ORION number from Section 9.7 does that
ratio match?

### Step 2: an 8:1 incast into a drop-tail queue

```bash
sudo bash net.sh queue droptail
sudo bash incast.sh /tmp/dt 8 15
tc -n ch09-sw -s qdisc show dev ch09-srx      # dropped, backlog
```

Look for: zero marks (a FIFO cannot mark), thousands of drops, a queue that sits for most of the run
near the 500,000-byte limit, and a probe RTT tens of milliseconds above the idle RTT. A full 500,000-byte
queue at 100 Mbit/s is 40 ms of delay. Goodput is still close to the ceiling. Raw output:
`step2-incast/droptail_rep*/`.

**Question 2.** Convert the median queue depth into queueing delay and compare it with the probe's RTT.
Who pays this delay in an AI cluster, the incast's own flows or someone else? (Section 9.5's victim
flows, and Section 9.2's "which egress queue?")

### Step 3: the same incast into RED with ECN

```bash
sudo bash net.sh queue red    # red limit 500000 min 18750 max 187500 probability 0.2 ecn
sudo bash incast.sh /tmp/red 8 15
```

Look for: `marked` in the RED statistics, and `IpExtInCEPkts` at the receiver matching it packet for
packet. Drops should be zero or close to it. The queue should sit between Kmin and Kmax, a fraction of
drop-tail's depth, with goodput nearly unchanged. Raw output: `step2-incast/red-ecn_rep*/`.

**Question 3.** Section 9.3 says marking trades latency against throughput. What did this queue profile
gain and lose against drop-tail, and why does the link stay busy although the queue is short? (Hint:
compare the queue with the BDP.)

### Step 4: the same RED queue, senders without ECN

```bash
sudo bash net.sh ecn 0        # senders stop asking for ECN in their SYN
sudo bash incast.sh /tmp/noect 8 15
sudo bash net.sh ecn 1
```

Look for: the queue profile is unchanged, but the data now arrives as not-ECT
(`IpExtInNoECTPkts`), RED's `early` drop counter replaces `marked`, and TCP retransmits climb. The
only marks left belong to the probe's ECT(0) pings. Raw output: `step2-incast/red-nonect_rep*/`.

**Question 4.** This is the misconfiguration in Section 9.3: an ECN-enabled class carrying traffic that
is not ECN-capable, and the WRED curve drops it. On ORION's lossless class, what would those drops trigger
in a RoCE NIC, and which counters would you check first to find this fault?

### Step 5: the as-found profile

```bash
sudo bash net.sh queue asfound   # min 187500 max 750000: thresholds 10x the template, Kmax above the buffer
sudo bash incast.sh /tmp/af 8 15
```

Look for: a queue that grows well past the template's Kmax before marking starts, with far fewer
marks per second and a probe RTT close to drop-tail's. With Kmax above the 500,000-byte limit, RED can
reach the full queue before it marks at full probability, and then it tail-drops (`pdrop`). Raw output:
`step2-incast/asfound_rep*/`.

**Question 5.** Section 9.10 predicts that on `orion-be-leaf-r3` the as-found profile lets PFC handle
the incast while ECN marks only sporadically. This fabric has no PFC. What took PFC's place here, and what
does that tell you about where the as-found queue settles?

### Step 6: DCTCP (if your kernel has it)

```bash
sudo bash net.sh queue dctcp     # step marking: min 18750, max 20264, probability 1.0
sudo bash incast.sh /tmp/dc 8 15 dctcp     # every client runs iperf3 -C dctcp
```

Look for: a queue held near K = 18,750 B, with goodput at the ceiling and a mark rate of a few percent.
DCTCP cuts its window in proportion to the fraction of marked packets instead of halving it, so it
can run with a much smaller standing queue than cubic. `run.sh` skips this step when
`tcp_available_congestion_control` lacks `dctcp`. Raw output: `step2-incast/dctcp_rep*/`.

**Question 6.** DCQCN (Section 9.6) also reacts to the fraction of marked packets, through α. Using this
step, explain why the chapter's rules put Kmin at or below one BDP for a proportional controller.

### Step 7: fan-in

`run.sh` repeats the drop-tail and RED+ECN runs at N = 1, 4 and 16 senders for 10 s each. Look for:
drop-tail drops and its deep queue at every N; RED+ECN marks at every N, and whether its queue and drops
stay low at N = 16. With 16 flows of at least two segments each in flight, the window floor alone holds
more than the BDP. Raw output: `step7-fanin/`.

**Question 7.** Section 9.7's fill time is buffer / ((N − 1) × r). Which parts of it does a TCP incast on
this fabric follow, and which does it not? Why does ECN help less as N grows, and what does that say about
incast on ORION, where 12 senders start at line rate?

`run.sh` interleaves Steps 2 to 6: three repetitions of each configuration, with the starting
configuration rotated each round, so slow drift on the machine does not favour one configuration
(Section 9.11, item 4).

## 7. Check your results

```bash
python3 check.py results/<run-id>
```

It re-derives every number from the raw files and checks that `summary.json` agrees. Then it tests the
mechanisms: the bundle is complete and every client ran its full duration; the base RTT shows the netem
delay; one flow fills the bottleneck; no run beats the goodput ceiling or holds more than the buffer;
drop-tail drops and never marks; RED+ECN marks, every mark arrives as CE at the receiver, marks replace
drops, the queue sits between Kmin/4 and Kmax at under half drop-tail's depth, and goodput stays within
10 % of drop-tail; non-ECT senders are dropped early, not marked; the as-found queue is at least twice the
template's; DCTCP holds the queue near K at full goodput (SKIP if absent); the repetitions are
interleaved; and the fan-in results are consistent. It does not compare your numbers with ours.

## 8. Reference results

Not yet recorded. The reference machine runs the custom WSL2 kernel of
[docs/HANDS_ON_LABS.md](../../../../../docs/HANDS_ON_LABS.md) section 6, and that kernel has no modules
installed: `tbf`, `red`, `netem`, `bridge` and `tcp_dctcp` are all `=m` in its configuration, so
`setup.sh` stops with "missing qdisc". The reference run will be committed in
`results/wsl2-rtx4060-laptop/` once the reference kernel provides them. Your numbers will differ with
the CPU and the kernel; the check tests physical sense, not equality.

## 9. Clean up

```bash
sudo bash teardown.sh                         # kills ch09-* processes, deletes the ch09-* namespaces
ip netns list | grep ch09; ip link | grep ch09   # both should print nothing
```

## 10. Connect to the chapter

| Section | What this lab makes concrete |
|---|---|
| 9.2 Queues and buffers | Congestion lives in one egress queue (`ch09-srx`); a gauge sampled every 20 ms against cumulative drop and mark counters |
| 9.3 ECN and WRED | ECT(0) and CE in real packets; the Kmin/Kmax/Pmax profile of Figure 9.2 in `sch_red`; WRED drops non-ECT traffic in an ECN class; thresholds from the BDP |
| 9.6 DCQCN | A proportional controller (DCTCP) against a halving one (cubic) on the same marks |
| 9.7 Incast arithmetic | N:1 fan-in into one port; buffer measured in BDPs; why ECN cannot shorten the first burst |
| 9.10 Worked example | The template against the as-found thresholds, scaled by the BDP |
| 9.11 Experiment design | Two documented configurations differing in one variable, interleaved repetitions, counters snapshotted around every run |
