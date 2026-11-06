# Chapter 11 hands-on: multi-process training, run `wsl2-rtx4060-laptop`

Every number below is `[MEASURED]` by this run (step named in brackets) unless labelled `[MODELED]`, which means computed by the chapter's formulas from measured inputs. CPU ranks use gloo over loopback with 1 thread each; the model has 9,446,400 parameters (37.8 MB of FP32 gradients). Load average before/after: 0.67 0.20 0.07 1/412 1409 / 7.52 5.61 4.82 2/456 75119 (other jobs on the host add noise). Total run time 1614 s.

## Step 1: scaling (gloo, CPU)

| Ranks | Weak step (s) | Compute-only (s) | Exposed comm (s) | Weak eff. | Samples/s | Strong step (s) | Strong speedup | Strong eff. | Ring bytes/rank (MB) `[MODELED]` | Implied busbw (GB/s) | Peak RSS, all ranks (MiB) |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | 0.062 | 0.045 | 0.017 | 1.00 | 517 | 0.078 | 1.00 | 1.00 | 0.0 | n/a | 641.6 |
| 2 | 0.066 | 0.041 | 0.025 | 0.94 | 967 | 0.067 | 1.17 | 0.58 | 37.8 | 1.50 | 1305.6 |
| 4 | 0.105 | 0.052 | 0.053 | 0.59 | 1218 | 0.097 | 0.80 | 0.20 | 56.7 | 1.07 | 2583.6 |
| 8 | 0.190 | 0.090 | 0.100 | 0.33 | 1348 | 0.191 | 0.41 | 0.05 | 66.1 | 0.66 | 5190.8 |

All values `[MEASURED]` (Step 1) except the ring bytes, 2(n − 1)/n × gradient bytes `[MODELED]`. Weak scaling keeps 32 samples per rank; strong scaling keeps 64 samples per step. Replica parameter checksums identical on every rank: True `[MEASURED]`.

## Step 2: gradient bucket size (4 ranks)

| bucket_cap_mb | Buckets | Bucket sizes (bytes) | Step (s) |
|---|---|---|---|
| 1 | 9 | 4198400, 4198400, 4198400, 4198400, 4198400, 4198400, 4198400, 4198400, 4198400 | 0.108 |
| 5 | 5 | 8396800, 8396800, 8396800, 8396800, 4198400 | 0.102 |
| 25 | 2 | 29388800, 8396800 | 0.099 |
| 100 | 1 | 37785600 | 0.137 |
| default | 3 | 4198400, 29388800, 4198400 | 0.105 |

Compute-only step at 4 ranks: 0.052 s `[MEASURED]` (Step 1). Bucket counts are DDP's own record after its iteration-1 rebuild `[MEASURED]` (Step 2).

## Step 3: gradient accumulation with no_sync (4 ranks)

| Micro-batches per step | Step (s) | Per micro-batch (s) | Samples/s | Comm per step (s) | Comm share | Throughput vs k = 1 |
|---|---|---|---|---|---|---|
| 1 | 0.110 | 0.110 | 1164 | 0.058 | 0.53 | 1.00 |
| 2 | 0.152 | 0.076 | 1686 | 0.048 | 0.31 | 1.45 |
| 4 | 0.244 | 0.061 | 2095 | 0.036 | 0.15 | 1.80 |
| 8 | 0.550 | 0.069 | 1863 | 0.133 | 0.24 | 1.60 |

Comm per step = step − k × compute-only micro-batch time `[MEASURED]` (Steps 1 and 3).

## Step 4: GPU reference (1 rank, NCCL)

Step time 0.0080 s on the GPU against 0.0619 s for one CPU rank (7.7×), peak CUDA memory 168.6 MiB `[MEASURED]` (Step 4). A one-rank NCCL group moves no gradient bytes.

## Step 5: faults

| Run | Timeout (s) | Exit | Attempts | First notice by a peer (s) | Peer error | Lost steps | Restart R (s) | Final loss = uninterrupted |
|---|---|---|---|---|---|---|---|---|
| fault_kill_norestart | 30.0 | 1 | 1 | 0.06 | RuntimeError | n/a | n/a | None |
| fault_kill | 30.0 | 0 | 2 | 0.05 | RuntimeError | 2 | 3.16 | True (bit-exact) |
| fault_hang_t10 | 10.0 | 0 | 2 | 10.04 | RuntimeError | 2 | 13.62 | True (bit-exact) |
| fault_hang_t20 | 20.0 | 0 | 2 | 20.02 | RuntimeError | 2 | 23.88 | True (bit-exact) |

All `[MEASURED]` (Step 5). Faults fire on rank 2 just before step 23; checkpoints every 10 steps.

- fault_kill_norestart: `[../third_party/gloo/gloo/transport/tcp/pair.cc:525] Read error [127.0.1.1]:1933: Connection reset by peer`
- fault_kill: `[../third_party/gloo/gloo/transport/tcp/pair.cc:525] Read error [127.0.0.1]:27835: Connection reset by peer`
- fault_hang_t10: `[../third_party/gloo/gloo/transport/tcp/unbound_buffer.cc:81] Timed out waiting 10000ms for recv operation to complete`
- fault_hang_t20: `[../third_party/gloo/gloo/transport/tcp/pair.cc:534] Connection closed by peer [127.0.1.1]:1435`

## Step 6: lost work against checkpoint interval (4 ranks, 192 steps, 6 kills)

Kills at steps [50, 117, 121, 132, 145, 152]; step time 0.1176 s, median checkpoint cost C = 0.084 s, productive MTBF = 3.76 s `[MEASURED]`. Young/Daly τ_opt = √(2·C·MTBF) = 0.79 s = 6.8 steps `[MODELED]`; lowest measured checkpoint + lost-work overhead at K = 8 steps `[MEASURED]`.

| K (steps) | τ (s) | Lost steps per kill, measured | (s − 1) mod K `[MODELED]` | Mean lost (steps) | τ/2 (steps) `[MODELED]` | Ckpt overhead | C/τ `[MODELED]` | Lost-work overhead | (τ/2)/MTBF `[MODELED]` | Sum measured | Sum model | Restart R median (s) | Final loss = uninterrupted |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2 | 0.24 | [1, 0, 0, 1, 0, 1] | [1, 0, 0, 1, 0, 1] | 0.50 | 1.0 | 31.3 % | 30.2 % | 1.6 % | 3.1 % | 32.9 % | 33.4 % | 2.82 | True (bit-exact) |
| 4 | 0.47 | [1, 0, 0, 3, 0, 3] | [1, 0, 0, 3, 0, 3] | 1.17 | 2.0 | 16.9 % | 16.9 % | 3.6 % | 6.2 % | 20.5 % | 23.2 % | 2.72 | True (bit-exact) |
| 8 | 0.94 | [1, 4, 0, 3, 0, 7] | [1, 4, 0, 3, 0, 7] | 2.50 | 4.0 | 8.9 % | 8.9 % | 7.8 % | 12.5 % | 16.7 % | 21.4 % | 2.75 | True (rel. diff 0.00000015) |
| 16 | 1.88 | [1, 4, 8, 3, 0, 7] | [1, 4, 8, 3, 0, 7] | 3.83 | 8.0 | 4.8 % | 4.7 % | 12.0 % | 25.0 % | 16.7 % | 29.7 % | 2.62 | True (bit-exact) |
| 32 | 3.76 | [17, 20, 24, 3, 16, 23] | [17, 20, 24, 3, 16, 23] | 17.17 | 16.0 | 2.7 % | 2.6 % | 53.6 % | 50.0 % | 56.3 % | 52.6 % | 2.56 | True (bit-exact) |

Overheads are fractions of the useful compute time (192 × step time). R/MTBF does not depend on τ and is reported separately as the restart column. Measured values from Step 6 logs `[MEASURED]`. "Final loss = uninterrupted" means within a relative 1e-5 of the run with no faults; float sums on CPU are not guaranteed bit-exact across restarts, so the bit-exact result is shown too.
