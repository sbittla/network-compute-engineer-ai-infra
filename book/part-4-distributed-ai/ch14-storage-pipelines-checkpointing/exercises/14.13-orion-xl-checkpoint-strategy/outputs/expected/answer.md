# 14.13 — Checkpoint strategy for ORION-XL: worked solution

**YAML changes** to `orion_ckpt_inputs.yaml`: `params: 405.0e9`, `gpus: 4096`, `nodes: 512`,
`step_time_s: 20.0`, `pfs_write_GBps: 400`, `pfs_read_GBps: 800`, `commit_overhead_s: 3.0`,
`job_mtbf_h: 3.0` (canonical ORION-XL: 1,536 node-h / 512 nodes). Other values, including restart
components and 40 % hard failures, are unchanged. Everything below is `[MODELED]` from `[ILLUSTRATIVE]`
inputs.

**Key quantities.** S = 405e9 × 14 = **5.67 TB** (1.38 GB per GPU). T_pfs_w = 5,670 / 300 = 18.9 s.
Sync δ = 21.9 s. Async blocking = 1.38/25 + 0.5 = 0.555 s, δ = 0.555 + 0.03 × 21.9 = 1.21 s,
completion 22.5 s. Failures/day = 24 / 3 = **8**.

| Strategy | τ (steps) | Overhead | RPO max | E[resume] | Lost GPU-h/day (ckpt + fail) |
|---|---|---|---|---|---|
| async PFS | 180 s (9) | 0.67 % | 202 s | 905 s | 662 + 9,265 = **9,927** |
| async two-level | 140 s (7) | 0.49 % | 726 s | 900 s | 478 + 9,964 = **10,441** |
| sync local + drain | 300 s (15) | 1.32 % | 325 s | 900 s | 1,298 + 9,667 = **10,966** |
| sync PFS | 700 s (35) | 3.13 % | 722 s | 905 s | 3,076 + 11,627 = **14,702** |

Hand check (async PFS): Young = √(2 × 1.212 × 10,800) = 161.8 s → 8.1 steps → **9 → 180 s**.

**Recommendation.** Asynchronous checkpoints to the PFS every 9 steps (3 min). Even so, ≈ 10.1 % of
98,304 GPU-h/day is lost. At M = 3 h, failures, not checkpoints, decide the economics.

**Capacity and retention.** 25 TB / 5.67 TB = 4.4, so at most **4** checkpoints: 3 validated + 1 in
flight = 22.7 TB (2.3 TB headroom). Retention counts *validated* checkpoints only. Never delete the last
validated one while the next persists. Archive one checkpoint per hour to the object store.

**Targets.** RPO ≤ 5 min (achieved max 202 s). RTO 15 min (expected 905 s, at the limit: justify it or
improve it).

**PFS burst other tenants see.** 5.67 TB in 18.9 s at the full 300 GB/s effective, plus a 3 s commit,
every 180 s: ≈ 12 % duty cycle and 7.9 % of write capacity on average. Other tenants see about 22 s of
saturated writes every 3 min. Propose bandwidth limiting, a dedicated checkpoint tier, or local/peer
staging.

**Highest-leverage improvement: time-to-resume.** The failure cost is 9,265 of 9,927 GPU-h/day, and
8 × 905 s × 4,096 / 3,600 = 8,241 GPU-h/day of that is restart time. Cutting detection from 300 s to
60 s saves 8 × 240 × 4,096 / 3,600 = **2,185 GPU-h/day**, more than three times all checkpoint
overhead (662). Next come spare capacity (a declared spare pool or a pre-agreed shrink to a smaller DP),
pre-pulled images, faster rendezvous, and in-memory peer checkpointing (Gemini-style, which also shrinks
the τ/2 losses). At this failure rate, elastic or fault-tolerant training that avoids full-job restarts
(Chapter 19) is the structural fix.
