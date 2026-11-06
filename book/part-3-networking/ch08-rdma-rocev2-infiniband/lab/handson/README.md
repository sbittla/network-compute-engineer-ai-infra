# Chapter 8 hands-on lab: real RDMA verbs with Soft-RoCE

## 1. What you will do

You create a real RDMA device on one Linux machine with Soft-RoCE (`rdma_rxe`, the kernel's software
RoCEv2 transport), read it the way an operator reads `mlx5_3` on an ORION node (`rdma link`,
`ibv_devinfo -v`, the GID table), and run the chapter's tools against it: `ibv_rc_pingpong`, then
`ib_write_bw`, `ib_write_lat`, `ib_read_lat` and `ib_send_lat` across message sizes. You change the
netdev MTU and the path MTU and watch `active_mtu`, packets per message and bandwidth move. Then you
break it the ways RDMA breaks in production (a wrong device name, no server, a wrong GID index, a
locked-memory limit, a peer that disappears mid-transfer) and read the evidence each failure leaves.

## 2. What is real here, and what is not

Real: the verbs objects (protection domains, memory regions with `lkey`/`rkey`, RC queue pairs walked
through RESET → INIT → RTR → RTS, completion queues), the GID table and its RoCE v2 type, perftest and
rdma-core exactly as on a GPU node, real memory registration (pinning) against a real
`RLIMIT_MEMLOCK`, real IBA packetization by path MTU, a real per-QP ACK timer and retry counter, and
the same completion status (12, `IBV_WC_RETRY_EXC_ERR`) NCCL logs. Every number in the reference
results is `[MEASURED]` on the reference machine.

Not real, or not ORION:

- **No NIC, no wire, no switch.** Soft-RoCE builds and parses RoCEv2 packets (UDP port 4791) in the
  kernel on the host CPU. With one rxe device in loopback, server and client share that device and
  packets never leave the host: there is no PFC, no ECN, no DSCP-to-queue mapping, no switch MTU and no
  packet loss unless you cause it. A host `tcpdump` would still see nothing on `ch08-v0`.
- **CPU-bound numbers.** Bandwidth is set by how many packets per second one CPU can build, checksum
  (ICRC) and copy: a few Gb/s to about 15 Gb/s here, against ORION's 392 Gb/s per rail. Latency is tens
  of microseconds, against ORION's ≈ 1.9 µs. Do not compare absolute values with Table 8.7. What does
  carry over: the shape of the bandwidth curve (a small-message rate limit, a plateau, n½), packet count
  set by path MTU, the GID rules, failure signatures and the ACK-timeout arithmetic.
- **One host.** Both ends sit on one rxe device, so a wrong GID that would be unroutable on a fabric (a
  link-local `fe80::` entry) still works here; Step 6 shows this and says why it would fail between nodes.
  Soft-RoCE between network namespaces on one host does not work (rxe sends from the initial namespace),
  so this lab does not pretend to have two nodes.
- **rxe is not a hardware NIC.** It has one RoCE v2 GID per address (no RoCE v1 entries, so the
  chapter's index 2 versus 3 trap cannot appear), reports `fw_ver 0.0.0`, and treats `retry_cnt = 7` as
  "retry forever" (its source, `drivers/infiniband/sw/rxe/rxe_comp.c`, skips the decrement at 7), where
  Table 8.3 assumes a hardware NIC gives up after 7 retries. Step 7 measures both behaviours.

The Level 3 extension in [../README.md](../README.md) (Section 8) runs perftest between two real nodes on
a lab fabric; that is where the absolute numbers, GPUDirect and switch MTU are tested.

## 3. Requirements

| Item | Need |
|---|---|
| GPU | No |
| Docker | No |
| Root | Yes: creating the veth pair and the rxe device, `setpriv` for the unprivileged runs |
| Kernel | Soft-RoCE: `CONFIG_RDMA_RXE` built in or the `rdma_rxe` module. Stock WSL2 kernels lack it; see [docs/HANDS_ON_LABS.md](../../../../../docs/HANDS_ON_LABS.md) section 6. Ubuntu: `linux-modules-extra-$(uname -r)` |
| Disk, RAM | < 10 MB of results; < 200 MB of RAM |
| Time | setup < 1 min (packages already present) to 2 min; run about 8 min |

## 4. Safety

- The lab creates one veth pair (`ch08-v0`/`ch08-v1`, both in the initial namespace), gives `ch08-v0`
  the address `10.208.0.1/32` (a host route only, no subnet route), and adds one rxe device
  `ch08rxe0` on it. It changes the MTU of `ch08-v0`/`ch08-v1` only. It never touches `eth0` or any other
  real interface, route or firewall rule.
- Every perftest process names `-d ch08rxe0` on its command line and runs under `timeout`;
  `teardown.sh` kills exactly those, deletes the rxe link, then the veth pair, and verifies all three are
  gone. `run.sh` calls it on exit, also after a failure.
- Step 6 runs perftest as uid 65534 (`nobody`) with a reduced `ulimit -l` in a subshell; the host's
  limits are not changed. Step 7 kills its own perftest server with `SIGKILL`.
- perftest on a real fabric saturates links and can trigger PFC (Section 8.10, Safety). Here it only
  loads CPUs; still, do not run it on a machine whose other work you care about timing.

## 5. Setup

```bash
cd book/part-3-networking/ch08-rdma-rocev2-infiniband/lab/handson
sudo bash setup.sh          # rdma-core, ibverbs-utils, perftest (pinned for Ubuntu 24.04); checks rdma_rxe
sudo bash run.sh my-run     # the whole lab, unattended (about 8 min) -> results/my-run/
python3 check.py results/my-run
```

From the repository root on Windows: `python scripts/handson.py setup ch08`, `... run ch08 my-run`,
`... check ch08 my-run`.

To follow the steps by hand, create the device first and keep it until you run `teardown.sh`:

```bash
sudo ip link add ch08-v0 type veth peer name ch08-v1
sudo ip addr add 10.208.0.1/32 dev ch08-v0
sudo ip link set ch08-v0 up && sudo ip link set ch08-v1 up
sudo rdma link add ch08rxe0 type rxe netdev ch08-v0
```

Why a veth end and not `eth0` or a `dummy` interface: rxe attaches to any Ethernet netdev, and a veth
end is built into every kernel, can take any MTU, and is yours to change. `dummy` is a module that the
custom WSL2 kernel does not ship, and `eth0` is the host's real interface, whose MTU you must not touch.

Each perftest run needs a server and a client. Run the server first (in a second terminal or with `&`),
then the client with the server's address as the last argument. Both use `-d ch08rxe0`; `-x` is the GID
index (Step 2 tells you which).

## 6. Steps

Write your answers in `results/<run-id>/answers.md`.

### Step 1: build a Soft-RoCE device and read it

```bash
ibv_devices                          # before: no devices
rdma link show                       # link ch08rxe0/1 state ACTIVE physical_state LINK_UP netdev ch08-v0
ibv_devinfo -v -d ch08rxe0           # transport, fw_ver, max_qp, max_mr, port state, max_mtu, active_mtu, link_layer
```

Look for: `transport: InfiniBand (0)` together with `link_layer: Ethernet`; `active_mtu` 1024 with
`max_mtu` 4096 on a 1500-byte netdev; `vendor_id 0xffffff` and `fw_ver 0.0.0` (no firmware: this is
software). Raw output: `step1-device/`.

**Question 1.** A colleague says "`transport: InfiniBand` means this is an InfiniBand device, not RoCE."
What do you answer, and which field settles it?

### Step 2: the GID table, and the smallest end-to-end proof

```bash
P=/sys/class/infiniband/ch08rxe0/ports/1
for i in 0 1 2 3; do echo "$i $(cat $P/gids/$i) $(cat $P/gid_attrs/types/$i 2>/dev/null)"; done
ibv_rc_pingpong -d ch08rxe0 -g 1 &          # server
ibv_rc_pingpong -d ch08rxe0 -g 1 10.208.0.1  # client
```

Look for: index 0 is the link-local `fe80::` GID built from the MAC address, index 1 is
`0000:...:ffff:0ad0:0001`, the IPv4-mapped GID for 10.208.0.1 (0x0a = 10, 0xd0 = 208), type `RoCE v2`.
Entries without an address read as zeros and their type file returns an error. The pingpong lines show
QP numbers, PSNs and the GIDs both ends used. Raw output: `step2-gids/`.

**Question 2.** Which GID index must `NCCL_IB_GID_INDEX` (or perftest `-x`) name on this host, and how
would you derive it on an ORION node where Section 8.4 puts `::ffff:10.100.3.3` at index 3? Why does this
table have no RoCE v1 entries, and why does that remove one of the chapter's failure modes here but not on
ORION?

### Step 3: bandwidth against message size, at two MTUs

```bash
sudo ip link set ch08-v0 mtu 1500    # then 9000; check: ibv_devinfo -d ch08rxe0 | grep active_mtu
ib_write_bw -d ch08rxe0 -x 1 -F -a -n 1000 --report_gbits &           # server
ib_write_bw -d ch08rxe0 -x 1 -F -a -n 1000 --report_gbits 10.208.0.1  # client
rdma statistic show link ch08rxe0/1                                   # sent_pkts before and after a run
rdma resource show qp link ch08rxe0/1                                 # while a transfer runs
```

`run.sh` runs the sweep three times at each netdev MTU, interleaved, counts packets for 10,000 64 KiB
WRITEs from `sent_pkts`, and captures the QPs mid-transfer. Look for: the 2-byte message rate (a CPU
property here, as it is a NIC property on ORION), the plateau, n½ (the smallest size reaching half the
plateau), 64 + 1 packets per 64 KiB WRITE at path MTU 1024 against 16 + 1 at 4096 (data plus one ACK,
both counted because one device is both ends), and the QP pair in `rdma resource`: the client's QP is in
RTS, the server's in RTR, because a WRITE target never sends. Raw output: `step3-bandwidth/`.

**Question 3.** The 4,096-byte path MTU gives about three times the plateau of 1,024 here, while Table 8.4
predicts only 5.6 % more payload on ORION. Explain both numbers with one idea, and say what it tells you
about which resource saturates first in rxe and in a 400 Gb/s NIC.

### Step 4: latency, one-sided against two-sided

```bash
ib_write_lat -d ch08rxe0 -x 1 -F -a &  ;  ib_write_lat -d ch08rxe0 -x 1 -F -a 10.208.0.1
ib_read_lat  -d ch08rxe0 -x 1 -F -a &  ;  ib_read_lat  -d ch08rxe0 -x 1 -F -a 10.208.0.1
ib_send_lat  -d ch08rxe0 -x 1 -F -a &  ;  ib_send_lat  -d ch08rxe0 -x 1 -F -a 10.208.0.1
```

Look for: `t_typical` (the median) and the 99 % and 99.9 % columns per size; where latency stops being flat
and starts growing with size; how `ib_read_lat` compares with `ib_write_lat` at 2 bytes (Section 8.10 says
a READ is a full round trip while the WRITE and SEND tests report half a ping-pong). Raw output:
`step4-latency/`.

**Question 4.** At which size does latency start to grow roughly linearly with size, and what does the
slope correspond to? Is the READ/WRITE ratio at 2 bytes what Section 8.10 predicts? If not, what in a
software transport could hide it?

### Step 5: path MTU, packets and the clamp

```bash
sudo ip link set ch08-v0 mtu 9000
for m in 256 512 1024 2048 4096; do
  ib_write_bw -d ch08rxe0 -x 1 -F -s 1048576 -D 3 -m $m --report_gbits &
  sleep 1; ib_write_bw -d ch08rxe0 -x 1 -F -s 1048576 -D 3 -m $m --report_gbits 10.208.0.1; wait
done
sudo ip link set ch08-v0 mtu 1500    # then ask for -m 4096 again and read the "Mtu" line
```

Look for: bandwidth rising with path MTU while the payload packet rate (bandwidth / MTU) changes far
less; at netdev MTU 1500, `-m 4096` silently runs at 1024, the `active_mtu` clamp of Section 8.7. Raw
output: `step5-mtu/`.

**Question 5.** Section 8.7 warns that MTU must agree at three layers. Which of the three did you just
change, which one does this lab not have at all, and what would a 1,500-byte switch port do to the
4,096-byte run on a real fabric that it cannot do here?

### Step 6: things that go wrong

```bash
ib_write_bw -d mlx5_0 -x 1 -F 10.208.0.1                 # a device name copied from another host
ib_write_bw -d ch08rxe0 -x 1 -F -p 18591 10.208.0.1      # nobody listening on that port
# empty GID (index 7), client only:
ib_write_bw -d ch08rxe0 -x 1 -F -s 65536 -n 1000 &  sleep 1;  ib_write_bw -d ch08rxe0 -x 7 -F -s 65536 -n 1000 10.208.0.1
# empty GID, both ends:
ib_write_bw -d ch08rxe0 -x 7 -F -s 65536 -n 1000 &  sleep 1;  ib_write_bw -d ch08rxe0 -x 7 -F -s 65536 -n 1000 10.208.0.1
# link-local GID (index 0), both ends:
ib_write_bw -d ch08rxe0 -x 0 -F -s 65536 -n 1000 &  sleep 1;  ib_write_bw -d ch08rxe0 -x 0 -F -s 65536 -n 1000 10.208.0.1
# (a failed client can leave its server waiting: kill %1, or wait for it, before the next pair)
# 8 MiB buffer, server as uid 65534 under ulimit -l 4096 / 8192 / 16384 / 65536 KiB, then as root at 4096:
sudo setpriv --reuid=65534 --regid=65534 --clear-groups bash -c \
  'ulimit -l 4096; ib_write_bw -d ch08rxe0 -x 1 -F -s 8388608 -n 20' &
ib_write_bw -d ch08rxe0 -x 1 -F -s 8388608 -n 20 10.208.0.1
sudo dmesg | grep ch08rxe0
```

Look for: which failures stop before any RDMA happens (device lookup, the TCP exchange of QP numbers,
GIDs and keys), and which happen in the QP transition (`Failed to modify QP ... to RTR`: the remote GID
and path MTU are set at INIT → RTR, Figure 8.4). For the locked-memory runs: the server fails with
`Couldn't allocate MR` / `Failed to create MR` only after the client connects (perftest registers after
the exchange), the kernel logs `rxe_reg_user_mr: returned err = -12` (ENOMEM), libibverbs warns about
`RLIMIT_MEMLOCK`, and the *client* reports only `Couldn't read remote address`. Root succeeds at the same
limit because `CAP_IPC_LOCK` bypasses it. Raw output: `step6-failures/`.

**Question 6.** Table 8.10 item 16 requires `ulimit -l` unlimited in the login shell, the Slurm job and
the container. Using your Step 6 results, explain why a check run as root on the node would pass while the
training job fails, and which side's log you must read to find the cause.

### Step 7: the peer disappears

```bash
# server and client with -n 2000000 (runs ~90 s); after 2 s kill the server process with SIGKILL, then:
rdma statistic show link ch08rxe0/1 | grep -o 'completer_retry_err [0-9]*'   # sample it every 50 ms
# repeat with -u 16, then with rdma_cm connection setup and a finite retry count:
ib_write_bw -d ch08rxe0 -R --retry_count=3 -F -s 65536 -n 2000000 &   # server (kill it after 2 s)
ib_write_bw -d ch08rxe0 -R --retry_count=3 -F -s 65536 -n 2000000 10.208.0.1
```

`-u` is the QP's local ACK timeout exponent (Section 8.6: T_ack = 4.096 µs × 2^timeout); perftest's
default is 14 and its default `retry_cnt` is 7. Look for: after the kill, `completer_retry_err` counts
one retransmission timeout per T_ack, so the interval between increments measures T_ack directly; with
`retry_cnt` 7 rxe never gives up and the client hangs; with `retry_cnt` 3 the client fails with
completion status 12 and `retry_exceeded_err` increases by one. Raw output: `step7-ack-timeout/`.

**Question 7.** Compare your measured intervals with Table 8.3. From the rdma_cm run, estimate the ACK
timeout that librdmacm chose. What would NCCL's default (`NCCL_IB_TIMEOUT` 20, `retry_cnt` 7) mean for a
job whose peer node has died, on a hardware NIC and on rxe?

## 7. Check your results

```bash
python3 check.py results/<run-id>
```

It re-parses the raw outputs and prints PASS/FAIL per check: the device and its MTUs, the GID table, a
connected RC QP pair, bandwidth and latency sweeps that are physically sensible (small messages far below
the plateau, MTU 4096 clearly above 1024, 17 and 65 packets per 64 KiB WRITE), every failure with its
signature, the memlock threshold between failing and passing limits, retry intervals within the band of
4.096 µs × 2^timeout, status 12 with a finite retry count, and a `summary.json` that agrees with the raw
files. It does not compare your numbers with ours.

## 8. Reference results

The reference run is in [results/wsl2-rtx4060-laptop/](results/wsl2-rtx4060-laptop/) (Intel i7-13700HX
under WSL2, kernel 6.18.54.1-rxe+, rdma-core 50.0, perftest 24.01.0); `report.md` there lists every
number with its step. Highlights, all `[MEASURED]`:

| Step | Result |
|---|---|
| 1 Device | `ch08rxe0` ACTIVE, link layer Ethernet; active MTU 1024 at netdev MTU 1500, 4096 at 9000 |
| 2 GID table | RoCE v2 IPv4-mapped GID at index 1 (10.208.0.1); `ibv_rc_pingpong` 73 µs per iteration |
| 3 `ib_write_bw` plateau | 3.59 Gb/s at path MTU 1024, 9.98 Gb/s at 4096; 65 vs 17 packets per 64 KiB WRITE |
| 4 Latency, 2 B | WRITE 10.0 µs, READ 10.6 µs, SEND 21.8 µs |
| 5 Path MTU sweep, 1 MiB WRITEs | 256 B → 0.66 Gb/s up to 4096 B → 5.98 Gb/s; the packet rate stays at 0.18–0.32 M pkt/s |
| 6 Failure signatures | wrong device, no server, GID-type mismatch, QP stuck before RTR, and an `RLIMIT_MEMLOCK` too small for the MR: each reproduced with its error text |
| 7 ACK timeout | timeout 14: retries every 68 ms (model 67 ms); timeout 16: every 287 ms (model 268 ms); `retry_cnt` 3 via rdma_cm gave status 12 (retry exceeded) after 2.2 s |

Soft-RoCE runs the transport on the CPU, so the cost is per packet, not per byte. The packet rate holds
at roughly 0.2–0.3 M packets/s whatever the MTU, and bandwidth therefore grows almost in proportion to
the path MTU. That is the chapter's case for a 4096 B path MTU, magnified. Section 8.6's ACK-timeout
formula, 4.096 µs × 2^timeout, predicts the measured retry intervals to within 7 %. On a real NIC the
bandwidth and latency would be 10–100× better. The verbs objects, the GID selection, the failure
signatures and the timeout arithmetic are the same.

Your numbers will differ with the CPU, the kernel and whatever else the machine is doing; the check tests
physical sense, not equality.

## Troubleshooting

- **`setup.sh`: "this kernel has no Soft-RoCE (CONFIG_RDMA_RXE)".** Stock WSL2 kernels lack it: build the
  kernel in [docs/HANDS_ON_LABS.md](../../../../../docs/HANDS_ON_LABS.md) section 6. On Ubuntu install
  `linux-modules-extra-$(uname -r)`.
- **"this step needs root: run with sudo".** `setup.sh`, `run.sh` and `teardown.sh` all call `need_root`.
- **"missing command: ib_write_bw (run setup.sh)".** perftest or rdma-core is not installed; run
  `sudo bash setup.sh`, which falls back to the distribution's versions if the pinned ones are absent.
- **`rdma link add` or `ip link add ch08-v0` fails with "File exists".** A previous run left the device:
  `sudo bash teardown.sh` (it kills every perftest on `ch08rxe0`, then removes the rxe link and the veth).
- **A manual client fails with "Couldn't connect" or hangs.** Start the server first and give it a
  second to listen; a server left behind by a failed run holds the port, so kill it or use `-p <port>`.
- **On WSL2, a raw file under `/mnt/d` cannot be created.** `run.sh` stages raw output in `/tmp` and
  copies it at the end for this reason; when running by hand, write to `/tmp` and copy afterwards.

## 9. Clean up

```bash
sudo bash teardown.sh       # kills ch08rxe0 perftest processes, deletes rdma link ch08rxe0 and veth ch08-v0
rdma link show; ip link show ch08-v0     # both should show nothing
```

## 10. Connect to the chapter

| Section | What this lab makes concrete |
|---|---|
| 8.2 The verbs model | PD, MR registration and its locked-memory limit, the RC QP states (RTR vs RTS in `rdma resource`), completion status 12 |
| 8.4 RoCEv2 | GID table, IPv4-mapped GIDs, RoCE v2 type in sysfs, UDP encapsulation in software |
| 8.6 Transport behaviour | The local ACK timeout 4.096 µs × 2^timeout and the retry budget, measured |
| 8.7 Path MTU | `active_mtu` from the netdev MTU, the 1,024 clamp, packets per message, packet rate as the limit |
| 8.10 Tools | `rdma link`, `ibv_devinfo`, `ibv_rc_pingpong`, perftest options `-d -x -a -s -n -D -m -u -R -F --report_gbits` |
| 8.13 Troubleshooting | Reading failure signatures on both ends; a discriminating test changes one thing |
| Table 8.10 | Items 1 (devices), 4 (MTU), 6 (GID selection) and 16 (locked memory) on a live device |
