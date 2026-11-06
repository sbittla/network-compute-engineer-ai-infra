# O1 — Analyze the synthetic time series (worked solution)

All values are medians over each episode, computed as **rates** from the lab's cumulative counters,
`[SIMULATED / SYNTHETIC data]`. `solve.py` computes them independently of the lab code; its
`episode_values.csv` holds every quoted number. Relies on manuscript Section 9.8 (Table 9.6 signatures,
Figure 9.10 decision tree, "Reading counters correctly") and lab README Tasks 1–3.

**Rate handling that matters:** the first sample of each series is NaN. The counter reset on
`orion-be-leaf-r4:eth1/2` at t = 200 s gives NaN for that interval, not a huge negative rate. The
`orion-be-spine-2` gap (300–310 s) is divided by the true 14 s, not 2 s. Dividing by 2 s inflates spine-2
pause rates 7×.

Episodes (hot = TC 3 watermark ≥ 1,000 KB or pause tx/rx ≥ 100/s, merged across ≤ 6 s gaps):
**100–158 s, 250–318 s, 400–468 s**.

## Episode 1 (100–158 s): **incast**, root `orion-be-leaf-r3:eth1/5` (toward `orion-n05`)

| Discriminating value | Value | Why it discriminates |
|---|---|---|
| eth1/5 egress | **393.6 Gb/s** (line rate) | A storm would show ≈ 0 Gb/s toward the device |
| eth1/5 TC 3 watermark | **≈ 1,426 KB** median (1,107–1,690 KB) | Held near the 1,000 KB aggregate Xoff-equivalent by PFC; peaks cross the 1,500 KB Kmin |
| eth1/5 ECN marks | **median 0** (IQR 0–27 k/s) | Sporadic: Kmin sits above Xoff, so marking starts only on overshoot peaks. On a template leaf this would be heavy marking |
| eth1/5 pause rx | **0 /s** | Not paused by its peer, so it is the root, not a branch |
| Sender ports (12 of them) pause tx | ≈ 16,500–19,100 /s port medians (eth1/1: 19,145 /s); fabric ports 0 /s | Pause stays at the first hop: no propagation; senders paused most of the time |
| `orion-n05 mlx5_3` `cnp_sent` | median ≈ 11 /s (mean ≈ 8,000 /s) | Little DCQCN feedback: the incast is handled by PFC (marks/pause ≈ 0.09) |

## Episode 2 (250–318 s): **pause propagation**, root `orion-be-leaf-r3:eth1/10` (toward `orion-n10`)

| Discriminating value | Value | Why it discriminates |
|---|---|---|
| eth1/10 egress, watermark, pause rx | 394.1 Gb/s, 1,374 KB (PFC-held), **0 /s** | Congested and not paused: the root |
| leaf-r3 uplinks pause tx to spines | **≈ 7,970 /s** (eth1/33), ≈ 8,080 /s (eth1/41) | Pause on switch↔switch links means the tree has spread |
| Spine ports toward leaf-r3 | queue ≈ 2,360–2,490 KB, **≈ 5.9–6.0 M marks/s**, *receiving* ≈ 8,000 pause/s | Deep *and* paused, so branches, not roots |
| leaf-r4 uplinks to spines | queue ≈ 1,840–1,880 KB, pause rx ≈ 4,780–5,020 /s | The next branch upstream |
| leaf-r4 host ports (rail-4 NICs of n01–n08) | pause tx ≈ 2,590–3,050 /s | The tree reaches the senders |

Strong reports note that this is cross-rail traffic (rail-4 NICs → a rail-3 NIC), which hints at a
rank-to-rail mapping error (Chapter 13): plausible, not proven from this data.

## Episode 3 (400–468 s): **PFC storm**, source `orion-n12:mlx5_3`

| Discriminating value | Value | Why it discriminates |
|---|---|---|
| leaf-r3 eth1/12 pause rx | **≈ 23,730 /s** | Sustained pause from the device: the refresh rate of a held pause (K2) |
| eth1/12 egress | **0.03 Gb/s** | Nothing drains; incast would be at line rate |
| eth1/12 watermark / ECN | **3,995 KB flat**, **0 marks/s** | Queue pinned at its maximum with no marking |
| NIC `orion-n12 mlx5_3` `pfc_tx_p3` | **≈ 23,730 /s**, rx 0.03 Gb/s | Confirmed from the device's own counters (proven, not inferred) |
| Collateral | leaf-r3 pauses eth1/3 and eth1/6 (≈ 6,000 /s) | orion-n03 and orion-n06, peers of n12, are paused: HOL victims upstream |

## Not an episode (520–558 s): busy and healthy

`orion-be-leaf-r4 eth1/7` (toward `orion-n07`): 381 Gb/s, watermark 212 KB (just above that leaf's
150 KB Kmin), ECN ≈ 46,000 marks/s, **pause 0**. DCQCN is working. A detector that flags "high throughput"
or "ECN > 0" as congestion produces a false positive here.

## Common mistakes

Quoting raw cumulative counters. Dividing across the spine-2 gap by 2 s. Calling spine ports roots
because their queues are deep, when they are receiving pause. Labelling the 520–558 s window as incast.
