# 3.10 — Queues, stripes and packets

Method: manuscript Section 3.5 (`iostat -x`, Little's law, `%iowait` dilution) and Section 3.7 (packet
rates). Inputs are the live `iostat` and `vmstat` sections of `lab/data/snapshots/orion-n12.json`
`[SIMULATED]`; results `[MODELED]`, recomputed by `solve.py` from the snapshot.

**(a) Little's law** (queue = arrival rate × time in system):

```text
nvme3n1: 830 /s × 0.0486 s = 40.3   (reported aqu-sz 40.34)
md0    : 830 /s × 0.0491 s = 40.8   (reported aqu-sz 40.75)
```

The reported queues are self-consistent: ≈ 41 requests are outstanding, and almost all of them wait on
the one slow member.

**(b) md0 throughput.** 830 r/s × 512 KiB = 830 × 524,288 B = 435.2 × 10⁶ B/s = **435 MB/s**. Cross-check:
4 members × 830 r/s × 128 KiB = 424,960 KiB/s, the md0 `rkB/s`. Each 512 KiB array read is split into
four 128 KiB member reads, so the array is as slow as its slowest member.

**(c) With a healthy member (≈ 0.25 ms array latency).**

```text
throughput = concurrency ÷ latency × size = 41 ÷ 0.00025 s × 524,288 B ≈ 164,000 req/s × 524,288 B ≈ 86 GB/s
```

The queue depth would allow ≈ 86 GB/s, far above what four Gen4 x4 drives can deliver: their links total
4 × 7.88 = 31.5 GB/s raw, and media limits are lower still. The loader only needs ≈ 0.73 GB/s, so with a
healthy member storage stops being the bottleneck and the limit moves back to GPU compute.

**(d) `%iowait` against `vmstat b`.** Mean live `b` = (14 + 14 + 16 + 17) / 4 = 15.25 blocked tasks;
15.25 ÷ 224 CPUs = **6.8 %**, consistent with the reported 6.90 % `%iowait`. Fifteen stalled loader
workers on a 224-CPU host look like single-digit iowait.

**(e) Frontend packet rate at 200 Gb/s.** Each frame carries 38 B of wire overhead (preamble 8 + Ethernet
header 14 + FCS 4 + inter-frame gap 12):

```text
MTU 9000: 200e9 ÷ 8 ÷ (9000 + 38) = 2.77 Mpps
MTU 1500: 200e9 ÷ 8 ÷ (1500 + 38) = 16.3 Mpps
ratio     = 9038 ÷ 1538           = 5.9×
```

At MTU 1500 the host must process ≈ 5.9× more packets (interrupts, softirq work) per second for the same
bandwidth, which is why a wrong MTU (as on `orion-n19`'s `rail3`) costs CPU time as well as RDMA MTU.
