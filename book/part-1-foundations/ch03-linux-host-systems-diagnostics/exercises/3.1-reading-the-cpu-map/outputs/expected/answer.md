# 3.1 — Reading the CPU map

Sources: manuscript Section 3.2 ("Sockets, cores, threads, and NUMA nodes", Figure 3.1) and the reference
snapshot `lab/data/snapshots/orion-n01.json` (`[SIMULATED]`). `solve.py` derives both answers from that
snapshot.

**(a) SMT siblings on socket 1.** The HX8 has 2 sockets × 56 cores × 2 threads = 224 logical CPUs. Linux
numbers the first hardware thread of every physical core first (0–111: 0–55 on socket 0, 56–111 on socket
1), then the second threads (112–223) in the same order, so the sibling of CPU *k* is *k* + 112. Socket 1's
physical cores therefore have first threads **56–111** and SMT siblings **168–223**, matching
`NUMA node1 CPU(s): 56-111,168-223`.

**(b) `taskset -c 56-63` for rank 2.** GPU 2 is `3a:00.0` (`nvidia-smi` index 2). Its PCIe switch (SW1)
hangs off **socket 0**: `pcie_sysfs` reports `numa_node=0`, and bus 0x3a is below 0x80. CPUs 56–63 belong
to socket 1, so the rank's main thread, and its pinned host buffers by first touch, sit on the wrong
socket. Every host-to-device copy and kernel launch then crosses the inter-socket link (UPI-class),
which raises latency and lowers effective H2D bandwidth. Bind it to socket-0 cores instead, a slice of
0–55 (plus their siblings 112–167 if the launcher uses SMT), ideally from the topology mapping of
Chapter 5.

**Common wrong answer:** assuming "CPUs 0–111 are socket 0" (true only on systems that enumerate SMT
siblings adjacently; always read `lscpu`).
