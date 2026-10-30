# Lab 13 — Cross-Layer Straggler Diagnosis (GPU, data, and network)

## 1. Goal and the real-world task it mirrors

"GPU utilization is fine, the network is busy, and the job is slow" is a weekly escalation in every AI
infrastructure team. The on-call engineer pulls per-rank, per-step telemetry and must say, with
evidence, whether the cause is communication, synchronization (a straggler), or data imbalance — and
which team owns the fix. You will build that analysis on a telemetry bundle from a 64-rank job on
eight ORION nodes and write the cross-layer diagnosis that is this chapter's deliverable.

## 2. Tier and realism boundary

**L1** (laptop, < 5 s). The bundle is `[SIMULATED]`; column meanings and units are in Section 3 below
and in `data/job_manifest.yaml`. Real telemetry has gaps, clock skew, counter resets, and interacting
causes that this bundle does not; see the manuscript's "Realism boundaries".

## 3. Setup

```bash
cd book/part-4-distributed-ai/ch13-gpu-data-movement/lab
python -m pip install -r ../../../../requirements.txt
python check.py                        # progress meter for starter/telemetry_diag.py
```

Inputs: `data/telemetry.csv` (3,840 rows: 60 steps × 64 ranks) and `data/job_manifest.yaml` (rank
mapping, units).

| Column | Meaning (units) |
|---|---|
| `step`, `rank`, `host`, `local_rank` | Step index; global rank; node (`orion-n17`…`n24`); GPU = NIC = rail index |
| `tokens` | Tokens processed by the rank this step |
| `dataloader_wait_ms` | Time the loop blocked waiting for the next batch |
| `compute_ms` | Forward + backward kernel time |
| `wait_ms` | Time inside the all-reduce before the last rank arrived (synchronization skew) |
| `comm_ms` | All-reduce data movement after the last rank arrived |
| `step_ms` | Wall-clock step, identical for all ranks. `step_ms − (dataloader_wait_ms + compute_ms + wait_ms + comm_ms)` ≈ 25 ms is the optimizer step |
| `gpu_util_pct` | % time any kernel ran (`utilization.gpu` style — NCCL kernels count while spinning) |
| `sm_active_pct` | % SM cycles active (DCGM SM-active style) |
| `sm_clock_mhz`, `gpu_temp_c`, `power_w`, `clocks_event_reason` | GPU clock (MHz), temperature (°C), power (W), active clocks-event reason |
| `nic_tx_gbps`, `nic_rx_gbps` | NIC rates averaged over the step (Gb/s) |
| `nic_retx` | Per-step delta of `packet_seq_err` + `local_ack_timeout_err` (sender) + `out_of_sequence` (receiver); see manuscript Table 13.4a |

## 4. Background

Manuscript Sections 13.6 (overlap), 13.7 (stragglers, amplification, instrumentation), 13.8 (the
three causes and the `utilization.gpu` trap), 13.9 (the method), 13.13 (worked incident).

## 5. Tasks

1. **Per-step statistics (10 pts).** `per_step_stats`: median/max compute, slowest rank, straggler
   ratio, sync overhead, wait, transfer, step time.
2. **Robust outliers (20 pts).** `robust_z`, `find_stragglers`, `onset_step`, `rank_onset`.
   *Acceptance:* the persistent stragglers and their onsets match the checker.
3. **Attribution (20 pts).** `attribute_cause`, using clocks/clocks-event reasons, tokens, and
   retransmissions — never compute time itself.
4. **Rails and decoys (15 pts).** `rail_health` (group by local rank = rail) and `hot_not_throttled`.
5. **Cost and symptom (10 pts).** `amplification` and `symptom_windows` (including burst NIC rate).
   Run `python starter/telemetry_diag.py` to print everything.
6. **Report (25 pts).** ≤ 2 pages: the annotated data-path diagram (Exercise 13.9), a findings table
   (cause, ranks/rail, onset, evidence fields, owner, safe fix, validation), the decoy and why it was
   rejected, the amplification numbers, and which metric would have misled you.

## 6. Running the checker

```bash
python check.py                    # your starter (TODO / FAIL / PASS per check)
python check.py --impl solution    # reference implementation (instructors)
```

## 7. Deliverable and grading rubric (100 pts)

| Item | Points |
|---|---|
| Tasks 1–5 (checker: 10 checks) | 75 |
| Report: findings table with independent evidence per finding | 10 |
| Report: annotated data-path diagram (GDR and host-staged variants) | 8 |
| Report: decoy rejected and misleading metric explained | 4 |
| Report: amplification and expected step time after fixes | 3 |

## 8. Extensions (L2/L3)

**L2 — instrument a real job (one 8-GPU host).** Add CUDA events around forward/backward and around
the gradient all-reduce in a small PyTorch DDP script launched with `torchrun --nproc-per-node=8`, log
tokens per rank, and sample hardware state in parallel:

```bash
nvidia-smi --query-gpu=index,clocks.sm,temperature.gpu,power.draw,utilization.gpu,clocks_event_reasons.active \
           --format=csv -l 1 > gpu_state.csv
dcgmi dmon -e 1002,1003,1004 -d 1000 > dcgm_prof.txt   # DCGM profiling: SM active, SM occupancy, tensor active
```

Field names and IDs are `[VENDOR-SPEC, 2026-10]`; older drivers name the clock field
`clocks_throttle_reasons.active`. Convert your logs to this lab's CSV schema and run your module on
them. Create imbalance *only in your own job* (give one rank longer sequences) and confirm the
detector finds it.

**L3 — validate the data path (two drained nodes).** Execute the measurement plan of manuscript
Table 13.5: `nvidia-smi topo -m`; `lsmod | grep nvidia_peermem` (or confirm the dma-buf path);
`sudo lspci -vvv -s <BDF>` for `ACSCtl` and `LnkSta`; perftest `ib_write_bw -d mlx5_2 --use_cuda=2
--report_gbits` (aligned) versus `--use_cuda=6` (misaligned) versus host memory; two-node nccl-tests
with `NCCL_DEBUG=INFO NCCL_DEBUG_SUBSYS=INIT,NET` (look for `/GDRDMA` on channel lines) and with
`NCCL_NET_GDR_LEVEL=LOC` as the GDR-off control. Run ≥ 5 repetitions each and record every field in
the manifest's L3 extension.

> **Safety:** Run all L3 steps on drained nodes. Do not change ACS, IOMMU, or kernel modules outside
> change control, and never throttle or power-cap GPUs in a shared job to "test" a hypothesis.

## 9. Intentionally flawed inputs

The bundle contains several planted causes with different onsets, two of which mask each other, and
one decoy. Instructor notes are in `../solutions/lab/README.md`.
