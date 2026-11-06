# Chapter 9 hands-on: ECN and incast with `tc` — `wsl2-rtx4060-laptop`

Every number is `[MEASURED]` on the machine in `environment.json`, in the step named; medians over the repetitions, with the range in brackets.

## Step 1: the fabric

- Bottleneck 100 Mbit/s; best TCP goodput through it 95.6 Mbit/s (1,448 payload bytes per 1,514-byte frame).
- Idle RTT probe → receiver: p50 **2.37 ms** (min 2.08) `[MEASURED, step 1]`, so BDP = 29,625 B `[MEASURED, step 1]`.
- One cubic flow into the drop-tail queue: **94.4 Mbit/s** (99 % of the ceiling), queue p50 142,414 B, 0 drops `[MEASURED, step 1]`.

## Steps 2–6: 8:1 incast, one queue profile at a time

Order of the interleaved runs: droptail_rep1 red-ecn_rep1 red-nonect_rep1 asfound_rep1 dctcp_rep1 red-ecn_rep2 red-nonect_rep2 asfound_rep2 dctcp_rep2 droptail_rep2 red-nonect_rep3 asfound_rep3 dctcp_rep3 droptail_rep3 red-ecn_rep3.

| Config | Goodput (Mbit/s) | Jain | Queue p50 (B) | Queue p99 (B) | Queue delay p50 (ms) | Probe RTT p50 / p99 (ms) | Drops | Marks | CE at receiver | Retransmits |
|---|---|---|---|---|---|---|---|---|---|---|
| droptail | 94.3 [94.2–94.3] | 0.984 | 466,410 [461,917–466,508] | 492,246 | 37.3 | 39.5 / 43.4 | 154 [141–155] | 0 [0–0] | 0 | 154 |
| red-ecn | 94.5 [94.4–94.6] | 0.998 | 30,378 [30,280–31,794] | 48,448 | 2.4 | 4.5 / 6.0 | 0 [0–869] | 3,574 [2,658–3,580] | 3,574 | 0 |
| red-nonect | 94.8 [94.7–94.8] | 0.999 | 30,280 [30,280–30,280] | 45,420 | 2.4 | 4.5 / 5.7 | 3,511 [3,492–3,523] | 18 [15–25] | 18 | 3,516 |
| asfound | 94.5 [94.4–94.9] | 0.992 | 190,862 [189,348–190,862] | 212,058 | 15.3 | 17.3 / 19.6 | 0 [0–0] | 322 [316–327] | 322 | 0 |
| dctcp | 94.7 [94.4–94.8] | 1.000 | 19,682 [19,682–19,682] | 35,594 | 1.6 | 3.6 / 4.9 | 23 [22–32] | 60,716 [60,501–60,792] | 60,716 | 0 |

All `[MEASURED, step 2–6]`. Queue figures are the bottleneck's backlog sampled every 20 ms after the first second; queue delay = backlog / drain rate.

red-nonect: senders with `tcp_ecn=0` into the same RED+ECN queue: 3,511 early drops, 18 marks (the ECT(0) ping probe only) `[MEASURED, step 4]`.

## Step 7: fan-in

| Config | N | Goodput (Mbit/s) | Jain | Queue p50 (B) | Drops | Marks | Retransmits |
|---|---|---|---|---|---|---|---|
| droptail | 1 | 94.5 | 1.000 | 132,524 | 0 | 0 | 0 |
| droptail | 4 | 94.3 | 0.996 | 442,284 | 27 | 0 | 27 |
| droptail | 16 | 93.3 | 0.984 | 471,050 | 325 | 0 | 322 |
| red-ecn | 1 | 94.3 | 1.000 | 15,140 | 0 | 108 | 0 |
| red-ecn | 4 | 94.4 | 0.999 | 24,224 | 0 | 1,046 | 0 |
| red-ecn | 16 | 93.7 | 0.998 | 46,934 | 17 | 5,697 | 0 |

All `[MEASURED, step 7]`, one run each (N = 8 is in the table above).

