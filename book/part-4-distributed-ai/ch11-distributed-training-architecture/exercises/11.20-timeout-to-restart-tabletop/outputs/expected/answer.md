# 11.20 — From timeout to restart (fault-isolation tabletop)

**Rank-to-hardware table** (Section 11.8 rule: node `orionxl-nNNN` hosts ranks 8(NNN − 1) … 8(NNN − 1) + 7;
local rank i ↔ GPU i ↔ NIC i ↔ rail i):

| Component | Node ranks | Implicated global rank | Rail |
|---|---|---|---|
| `orionxl-n312` GPU 5 (uncorrectable ECC, Xid 48-class) | 8 × 311 = 2488 … 2495 | 2488 + 5 = **2493** | 5 |
| `orionxl-n141` NIC 2 (14 link-down/up events) | 8 × 140 = 1120 … 1127 | 1120 + 2 = **1122** (GPU 2's traffic) | 2 |

**Timeline**

| Time | Event | Interpretation |
|---|---|---|
| 01:00 | n141 NIC 2 starts flapping | Rail-2 link instability (optic, cable or NIC port) |
| 01:05 | Step time +6 % on n141's ranks | Straggler: rank 1122's DP/PP traffic retries or reroutes; job degraded, not hung |
| 02:58 | Uncorrectable ECC on n312 GPU 5 | Fatal for the CUDA context on rank 2493 |
| ≈ 02:58–03:02 | Process of rank 2493 dies or wedges | Never joins the next collective |
| 03:12 | NCCL watchdog timeout on healthy ranks | ≈ 10–14 min after the ECC event: consistent with the default ≈ 10 min watchdog after the last completed collective |

**Health decisions.** Most likely cause of the timeout: **the ECC fault on n312 GPU 5** — fatal to the
process, and a timeout follows about one watchdog period later. The flapping NIC is **correlated but
separate**: the job ran 2 hours with it, slower but progressing. Quarantine: drain `orionxl-n312` (the
smallest schedulable domain for a TP = 8 job is the node); the GPU goes to Fleet for reset/row-remap/RMA
triage. Drain `orionxl-n141` and open a Fabric ticket for NIC 2's port, optic and cable (Chapter 10).

**Restart plan.** Restore the last checkpoint whose write completed and was validated **before
02:58** (conservative: ECC events can corrupt state before the crash). Replace the two nodes from a
declared ORION-XL spare pool (a variation from the reference cluster) or restart at a smaller DP with
batch/LR adjusted; keep the same rank map. Validate: loss within noise of the pre-incident trend, step
time back to the pre-01:05 baseline, no per-rank outliers, clean NIC counters on the replacements.

**What would prove the cause (vs correlation).** Flight-recorder dumps showing rank 2493 missing from,
or behind in, the collective that timed out (lowest sequence number), with the Xid timestamp preceding
it; the NIC flaps cannot explain a missing rank.
