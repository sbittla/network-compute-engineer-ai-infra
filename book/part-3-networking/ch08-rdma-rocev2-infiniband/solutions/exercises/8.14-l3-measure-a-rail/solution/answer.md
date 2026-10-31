# 8.14 — L3 extension: measure a rail (marking guide and model expectations)

There is no fixed answer: results are the learner's own `[MEASURED]` data. Relies on manuscript Section
8.7 (Table 8.4, wire-efficiency model), Section 8.10 (perftest), Section 8.11 (commissioning rail 3,
the n½ model) and lab README §8 (L3 variant). Safety: dedicated lab fabric only.

## What a complete submission contains

1. **Raw captures:** the unedited `ibv_devinfo`, `rdma link`, `show_gids`, `ethtool -i`, `ip`, `dcb`
   and `lsmod` captures from both nodes, the validator output (both nodes READY, or findings fixed
   first), and every `ib_write_bw -a` / `ib_write_lat -a` output.
2. **`manifest.yaml`** with `evidence_class: MEASURED` and every field the lab manifest asks to record:
   NIC model and firmware, driver/OFED and kernel versions, link speed and FEC mode, path MTU, switch
   model/OS and port MTU, the perftest version and exact command lines, CPU pinning, BIOS power settings,
   date.
3. **Method:** ≥ 2 rails; ≥ 5 repetitions per rail and test; warm-up run discarded; perftest pinned to the
   NIC's NUMA node (`numactl --cpunodebind=<n> --membind=<n>` or `taskset`); the same peer pair
   throughout; no competing traffic (state how this was checked).
4. **Statistics table:** for each rail, median and min/max of the bandwidth **plateau** and of **n½**
   (the message size reaching half the plateau), and median and min/max of small-message **p99 and
   p99.9** latency.
5. **Model-versus-measured table** with an explanation of any gap.

## Model values to compare against `[MODELED]`

Payload ceiling = link rate × 4,096 / (4,096 + 82) at path MTU 4,096, untagged IPv4 (Table 8.4):

| Link speed | Ceiling at 4,096 | Ceiling at 1,024 |
|---|---|---|
| 400 Gb/s | 392.1 Gb/s | 370.3 Gb/s |
| 200 Gb/s | 196.1 Gb/s | 185.2 Gb/s |
| 100 Gb/s | 98.0 Gb/s | 92.6 Gb/s |

Use the learner's *actual* link speed and MTU (add 4 B per packet with a VLAN tag, 20 B more for IPv6).
A measured plateau **1–3 % below** the ceiling is normal (ACKs, doorbells, PCIe overheads). More than
**5 % below** needs an explanation backed by a discriminating check:
- PCIe link width/speed: `lspci -vv` LnkSta vs LnkCap;
- NUMA placement;
- MTU actually negotiated (perftest's printed `Mtu`);
- CPU frequency scaling;
- competing traffic: switch port counters during the run.

## Marking notes

Award the "method" points only with ≥ 5 runs, warm-up discarded and pinning stated. Deduct where a
single run is reported as "the" result, or where the model uses 400 Gb/s for a 200 Gb/s lab link.
