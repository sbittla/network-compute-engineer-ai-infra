# Lab 7 L2: container-fabric probe and an ECMP hashing Monte Carlo for low-entropy RoCE flows

`[SIMULATED]` on **NVIDIA GeForce RTX 4060 Laptop GPU**, 2026-10-31T23:40:07Z.

| Environment | Value |
|---|---|
| device | cuda |
| cpu_model | 13th Gen Intel(R) Core(TM) i7-13700HX |
| cpu_count | 24 |
| mem_total_gib | 7.8 |
| os | Linux-6.18.54.1-microsoft-standard-WSL2-x86_64-with-glibc2.35 |
| torch | 2.5.1+cu124 |
| cuda_runtime | 12.4 |
| driver_version | 592.82 |
| pcie.link.gen.max | 4 |
| pcie.link.width.max | 8 |
| clocks.max.sm | 3105 |
| power.limit | [N/A] |

**Status:** ran
**Invariants:** all passed

## Section 7.6 reproduced: 8 RoCE flows hashed onto 8 equal-cost links `[SIMULATED]`

2,000,000 trials. P(all eight on distinct links) **0.242 %**; expected links used **5.252 of 8**.

| Most-loaded link carries | This run | Manuscript (200,000 trials) |
|---|---|---|
| 2 flows | 49.8 % | 49.9 % |
| 3 flows | 40.9 % | 40.9 % |
| 4+ flows | 9.0 % | 8.9 % |

## Simulation against closed form

| Quantity | Closed form `[MODELED]` | Simulated |
|---|---|---|
| p_all_distinct_8x8 | 0.0024 | 0.00242 |
| links_used_8x8 | 5.25113 | 5.25169 |
| links_used_32x32 | 20.41423 | 20.4178 |
| modulo_keep_32 | 0.03125 | 0.03135 |
| resilient_keep_of_survivors | 1.0 | 1.0 |

32 flows on 32 links: a link with >= 3 flows in **97.0 %** of trials.
Polarisation: with the leaf's hash reused at the spine, spine-1 used **2 of 8** links toward the destination leaf; with its own seed it used 8 of 8.
Link failure (32 -> 31 members): modulo rehash kept **3.1 %** of flows on their member; resilient hashing kept 100.0 % of the flows whose member survived.

Monte Carlo speed `[MEASURED]` on the GPU: 37,322,768 trials/s.

What to conclude: ECMP balances *flows*, not bytes. With the handful of flows an AI collective presents, collisions are the norm (some link carries two or more flows in over 99 % of trials), polarisation silently idles links, and a plain modulo rehash moves almost every flow when one member fails. None of this needs a fault to happen; it is why the book keeps collectives on rails, adds QPs, and asks for resilient hashing.

## Not runnable on this host

- **containerlab 2-spine x 4-leaf eBGP fabric (FRR): ECMP next-hop counts, BFD, reconvergence loss window**: needs a Linux host with containerlab and FRR images, the Docker socket, root / CAP_NET_ADMIN, network namespaces the lab may create (the harness runs with --network none). Probe: containerlab absent, Docker socket absent, CAP_NET_ADMIN no, interfaces ['lo'].

- [SIMULATED] ECMP hashing only: flows are independent, constant-rate and never adapt; there are no queues, ECN or PFC.
- Flows: random 10.x.y.z source/destination NICs, UDP source port per queue pair in 49152-65535, destination port 4791.
- Timing [MEASURED]: 5 repetitions of the 2000000-trial 8x8 batch after 1 warm-up; median 53.6 ms, p95 54.4 ms.
