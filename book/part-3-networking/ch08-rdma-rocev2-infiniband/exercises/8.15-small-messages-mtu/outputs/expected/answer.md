# 8.15 — Small messages work, large ones do not (worked solution)

Evidence is `[ILLUSTRATIVE]`; packet-size arithmetic `[MODELED]` (`solve.py` packetizes the whole
`ib_write_bw -a` sweep). Relies on manuscript Section 8.7 (MTU at three layers, frame layout), Section
8.10 (`ibv_rc_pingpong`, perftest), Section 8.6 (retry-exceeded), and docs/VERIFIED_FACTS.md
(`ibv_rc_pingpong` default path MTU 1,024).

## (a) Ranked hypotheses

1. **MTU mismatch on the replacement leaf's ports toward `rack-04`.** The ports restored from a
   template carry the default 1,500-byte MTU instead of 9216. Fits every item: a hard size threshold
   (≤ 1,024-byte messages work, larger fail), the rising **oversize/giant drop** counter on exactly
   those ports, the rack-scoped impact, and the timing (leaf replaced over the weekend).
2. **QoS/PFC misconfiguration on those ports** (trust or DSCP map lost, so RoCE is lossy). It would
   cause loss under *load*, not a clean size threshold in a two-node test, and it would not increment
   oversize drops.
3. **Faulty optics or cables.** Ruled down by zero FEC-uncorrectable and CRC errors, and by the clean
   size threshold (bit errors hit small packets too).

*Excluded by evidence:* host MTU. `ip -o link` shows 9000 and `ibv_devinfo` shows `active_mtu 4096 (5)`
on both nodes.

## (b) Two safe discriminating tests (drained nodes; read-only or low volume)

```bash
# 1. DF ping from orion-n13 to its leaf-side address 10.100.6.26 (= 10.100.6.(2 x 13)):
ping -M do -s 8972 -c 3 10.100.6.26     # 9,000-byte IP packet: expect 100 % loss if the leaf port is 1500
ping -M do -s 1472 -c 3 10.100.6.26     # 1,500-byte IP packet: expect 0 % loss
# 2. Same perftest sweep with the path MTU forced to 1,024:
ib_write_bw -d mlx5_6 -x 3 -a -F --report_gbits -m 1024 10.100.6.29   # server side runs the same with -m 1024
```

Expected: the full `-m 1024` sweep completes with a ≈ 370 Gb/s plateau (Table 8.4), while the default
(4,096) stalls after the 1,024 row. A third read-only step: ask the Fabric team to show the leaf port
configuration and MTU. Do not change it from the host incident.

## (c) Root cause and the exact mechanism

**Root cause:** the replacement leaf's ports to `rack-04` run at **MTU 1,500**. The QP path MTU is
4,096, so a RoCEv2 IP packet is 20 (IPv4) + 8 (UDP) + 12 (BTH) + [16 RETH on a first/only packet] +
payload + 4 (ICRC):

| WRITE message | Packets at path MTU 4,096 | Largest IP packet | At a 1,500-byte port |
|---|---|---|---|
| 1,024 B | 1 ("only" packet) | 1,024 + 60 = **1,084 B** | passes |
| 2,048 B | 1 | 2,048 + 60 = **2,108 B** | dropped |
| ≥ 4,096 B | ⌈m / 4,096⌉ | 4,156 B (first), 4,140 B (middle) | dropped |

These are IP-packet sizes, matching an EOS/NX-OS-style L3 `mtu`. Where the switch MTU counts the frame,
add 18 B (1,102 B and 2,126 B); the verdicts do not change. MTU semantics are vendor-specific.

So the perftest sweep prints every row **up to `#bytes 1024`** and then stops: every packet of the
2,048 row is dropped as a giant at the leaf ingress. No ACK ever returns, so the requester retries
(retry_cnt + 1) × T_ack and fails with **`IBV_WC_RETRY_EXC_ERR`**. NCCL's first large all-reduce
behaves the same way.

**Why `ibv_rc_pingpong` passes:** its **default path MTU is 1,024** (`-m` changes it), so its
4,096-byte SEND messages travel as four 1,024-byte packets (1,024 + 44 = **1,068 B** IP, no RETH), all
≤ 1,500. The "connectivity test" passes exactly because it avoids the failing size. Jobs without
`rack-04` nodes never cross those ports and stay healthy.

## (d) Safe fix and validation

**Fix (through the Fabric team, under change control):** raise a change for `orion-be-leaf-r6`. Set the
`rack-04`-facing ports to the ORION standard MTU **9216**, in a window with the affected nodes drained,
with a rollback plan. Diff the **whole** replacement leaf's configuration against the golden template
(other settings may also have reverted: trust, DSCP map, PFC). Add a port-MTU compliance check to the
switch-replacement runbook and to the intent validator (Lab 7 `MTU_MISMATCH`).

**Validation criteria:**
- `ping -M do -s 8972` to the leaf succeeds from every `rack-04` node (n13–n16);
- `ib_write_bw -a` on rail 6 from each `rack-04` node completes the full sweep at ≈ 390 Gb/s
  (≥ 95 % of 392 Gb/s);
- an NCCL job including `rack-04` completes with bus bandwidth in the normal band over ≥ 5 runs;
- the leaf's oversize-drop counter stops increasing (flat for 24 h).

## Common mistakes

Blaming host MTU despite the evidence. Treating pingpong's pass as proof of a healthy path. Changing
the switch MTU directly from the host incident without the Fabric team. Inventing flags (−2 points).
