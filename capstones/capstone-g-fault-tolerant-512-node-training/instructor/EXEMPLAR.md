# Capstone G — Abridged Exemplar of a Distinction-Level Submission (INSTRUCTOR ONLY)

> Abridged model answer in the learner's voice. Suggested score ≈ 92/100.

**Environment statement (page one):** All results below are `[SIMULATED]` on the synthetic ORION-XL
incident dataset shipped with the starter kit (seed 22). No real hardware was involved; log formats
imitate real tools and must be re-verified on a real platform.

---

## 1. What happened (true UTC)

| UTC | Evidence | Meaning |
|---|---|---|
| 02:34:07, 02:43:07, 02:52:07, 03:05:07 | `orionxl-n213` mlx5_3 link down/up (0.64 s); step times 9–12 s at those steps | Flaky rail-3 link; job survived each flap as a straggler |
| 03:10:39 | Async checkpoint 51,750 starts uploading (392 s needed at 2.5 GB/s) | Not durable until ≈ 03:17:11 |
| 03:14:03.8 | All ranks complete step 51,797 | Last progress |
| 03:14:07.000 | Xid 94 on `orionxl-n377` PCI `0000:ab:00` (GPU5) | Contained uncorrectable ECC error; process killed |
| 03:14:07.4 | rank 3013: "CUDA error: uncorrectable ECC error encountered" | Rank 3013 dies before enqueuing collective 1,203,456 |
| 03:14:45 | Automation alert | detect = 38 s |
| 03:18:09 | HCA quarantined, `orionxl-n213` drained | isolate = 242 s |
| 03:24:07–11 | ≈ 400 watchdog timeouts (600 s) | Symptoms, not causes |
| 03:29:19 | First step after restart from 51,474 | RTO = 912 s |

## 2. Proven cause versus correlation

| Claim | Verdict | Discriminating evidence |
|---|---|---|
| GPU5 on `orionxl-n377` caused the hang | **Proven** | Rank 3013 is the only rank with collective seq 1,203,455; Xid 94 + DBE on its GPU (BDF via inventory) 3.2 s after its last progress |
| The rail-3 HCA on `orionxl-n213` caused the hang | **Rejected as cause; independent fault** | Job progressed after every flap; `orionxl-n213` ranks reached seq 1,203,456 |
| `orionxl-n042` failed first | **Rejected (clock skew)** | chrony offset −180 s; corrected, its timeouts are at 03:24:07 like everyone else |
| `orionxl-n214`'s link is faulty | **Rejected (stale DCIM)** | LLDP shows port 22 is `orionxl-n213`; DCIM swap filed |

## 3. Containment

Quarantine GPU `orionxl-n377:5` (repair domain) and drain `orionxl-n377` (placement unit: TP = 8
needs eight GPUs). Xid 94 is contained, so in principle "drain when convenient"; the job was already
dead, so now was convenient. Reset activates the pending row remap; re-run acceptance (Capstone E)
before release. Quarantine HCA `orionxl-n213:mlx5_3`, drain the node (rail-aligned job needs all
eight rails), Fabric ticket on `orionxl-be-leaf-p06-r3` port 22 (inspect optic, clean, reseat).
Watch tickets: `orionxl-n101:2` (SBE 2,400), `orionxl-n099:2` (30 corrected AER).

## 4. Recovery

Checkpoints: 51,750 rejected (uncommitted, 34 shards missing), 51,612 rejected (shard 232 checksum),
51,474 restored. Spares: `n481` (acceptance pending) and `n482` (open GPU quarantine) excluded;
`orionxl-n213 → n483`, `orionxl-n377 → n484` (the automation paired them the other way round; either is valid); 16 ranks remapped with GPU index (and so rail)
preserved. Resume validation: first step 51,475; identical data-loader sample indices; maximum relative loss deviation 0.065 % (tolerance 0.1 %, set from replay noise) over 323
replayed steps; no NaN; progressed past 51,797 — **job resumed correctly**. The earlier drill that
restored 51,612 fails the same test (deviation 59 %, NaN at 51,950).

## 5. Metrics

| Measure | Value | Target | Met |
|---|---|---|---|
| Detect | 38 s | 120 s | yes |
| Isolate | 242 s | 600 s | yes |
| RTO | 912 s | 1,800 s | yes |
| RPO | 323 steps (1,405 s) | 276 steps | **no** |
| Lost | 2,471.5 GPU-h | — | — |

Model `[MODELED]`: expected loss per interruption ≈ 3,840 × (300 + 392 + 900) / 3,600 ≈ 1,698 GPU-h.
This incident lost 45 % more because a corrupted shard forced a restore one interval older.

## 6. Postmortem contributing factors and actions

1. Checksums verified only at restore → verify at commit, re-upload bad shards (Training Infra).
2. Durability lag 392 s → raise upload share during the first minute or keep two in-flight
   checkpoints (Storage), re-derive interval with δ and lag.
3. Stale DCIM record → nightly LLDP-vs-DCIM diff (Fabric).
4. Flapping HCA left in service 40 min → quarantine at ≥ 3 flaps/h automatically (Fleet).
5. Spare pool must exclude open quarantines and pending acceptance — already true in automation;
   make the scheduler enforce it too (Platform).

---

**Instructor note.** Distinction: page-one environment statement, discriminating evidence for each
claim, Xid 94/95 nuance, correct repair-versus-placement domain, RPO miss explained. Points lost for
no L2/L3 evidence and a thin security section in this abridged form.
