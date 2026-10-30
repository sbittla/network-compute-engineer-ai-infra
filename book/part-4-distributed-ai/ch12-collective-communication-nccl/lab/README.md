# Lab 12 — nccl-tests Analysis Toolkit (Progressive Lab 5)

## 1. Goal and the real-world task it mirrors

Every GPU cluster runs nccl-tests: at node acceptance, after maintenance, nightly, and during
incidents. Someone has to turn a folder of `all_reduce_perf` logs into answers: *Does the fabric
scale? Which runs are unhealthy, and is it a mapping problem or a broken link? What will our
training collectives cost?* You will build that analysis: a parser for the real nccl-tests text
format, algbw/busbw recomputation, latency/bandwidth region classification, an alpha-beta fit, a
jitter metric, and an anomaly detector — then write the collective benchmark report that is this
chapter's deliverable.

## 2. Tier and realism boundary

**L1** (laptop, < 2 s). The six logs in `data/` are `[SIMULATED]` from an alpha-beta model with noise;
they reproduce the format and the *shape* of real results, not NCCL's
actual algorithm switching, contention, or retransmission timing. The optional gloo script measures
your CPU and loopback TCP stack only.

## 3. Setup

```bash
cd book/part-4-distributed-ai/ch12-collective-communication-nccl/lab
python -m pip install -r ../../../../requirements.txt
python check.py                     # progress meter for starter/nccl_analysis.py
```

Inputs: `data/configs.yaml` (what each run was), `data/c1…c6_*.log` (nccl-tests output),
`data/nccl_debug_c2_2node_aligned.txt` and `data/nccl_debug_c3_2node_alt_map.txt` (NCCL INFO excerpts).

## 4. Background

Manuscript Sections 12.2–12.3 (collectives, alpha-beta), 12.5 (reading nccl-tests, busbw), 12.6–12.8
(NCCL internals, variables, rank mapping), 12.10–12.11 (discipline and the worked report).

## 5. Tasks

1. **Parse (15 pts).** Implement `parse_nccl_log`. It must handle the "Using devices" header (ranks and
   hosts), the warm-up/iteration header, the 13-column data rows (time printed with 2, 1, or 0
   decimals depending on magnitude), and the "Avg bus bandwidth" trailer. *Acceptance:* c2 → 31 rows,
   16 ranks, 2 hosts with 8 ranks each.
2. **Bandwidth (15 pts).** Implement `bus_factor` and `compute_bw` for all-reduce, all-gather,
   reduce-scatter, broadcast, reduce, and all-to-all. *Acceptance:* recomputed values match every
   printed algbw/busbw in c5 within rounding.
3. **Regions and plateau (15 pts).** Implement `plateau_busbw` and `classify_regions`.
   *Acceptance:* c2 has a monotonic latency → transition → bandwidth labelling; plateaus ≈ 450 GB/s
   (c1) and ≈ 346 GB/s (c5).
4. **Alpha-beta (15 pts).** Implement `fit_alpha_beta` (least squares weighted by 1/t) and
   `predict_time_us`. *Acceptance:* c2 → α ≈ 28 µs, B ≈ 355 GB/s, n½ ≈ 5.3 MB.
5. **Anomalies (15 pts).** Implement `jitter_cv` and `detect_anomalies`. Run
   `python starter/nccl_analysis.py` to print the summary. *Acceptance:* the checker's expected labels.
   Then open the two NCCL debug excerpts and explain, in your report, *why* the steady-low
   configuration is low.
6. **Report (25 pts).** The chapter deliverable, ≤ 2 pages: summary table, log-log plot of time vs
   size for at least c1, c2, c5 (matplotlib), scaling verdict, each anomaly with its signature and the
   evidence you would collect next, and the predicted cost of a 25 MB bucket and of W-TRAIN's DP
   reduction (Section 12.11).

## 6. Running the checker

```bash
python check.py                    # your starter (TODO / FAIL / PASS per check)
python check.py --impl solution    # reference implementation (instructors)
```

## 7. Deliverable and grading rubric (100 pts)

| Item | Points |
|---|---|
| Tasks 1–5 (checker: 10 checks) | 75 |
| Report: summary table and plot (labelled axes, units, log scales, evidence labels) | 8 |
| Report: scaling verdict with numbers (plateau and α vs nodes) | 6 |
| Report: anomalies explained with signature + next evidence (NCCL INFO, counters, pairwise tests) | 8 |
| Report: W-TRAIN cost predictions | 3 |

## 8. Extensions (L2/L3)

**Optional L1 (PyTorch installed):** `python optional/gloo_allreduce.py --world 4 > my_gloo.log`, then
parse `my_gloo.log` with your module. Label results `[MEASURED]` (laptop, gloo, loopback) and record
CPU model, core count, PyTorch version.

**L2 — one 8-GPU host.** Build nccl-tests (`make MPI=1 MPI_HOME=… CUDA_HOME=…` per its README), then:

```bash
nvidia-smi topo -m > topo.txt
NCCL_DEBUG=INFO NCCL_DEBUG_SUBSYS=INIT,GRAPH NCCL_TOPO_DUMP_FILE=topo.xml \
  ./build/all_reduce_perf -b 8 -e 8G -f 2 -g 8 > l2_allreduce_run1.log 2> l2_nccl_info.log
for i in 2 3 4 5; do ./build/all_reduce_perf -b 8 -e 8G -f 2 -g 8 > l2_allreduce_run$i.log; done
```

(`-g 8` runs 8 GPUs from one process.) Parse all five runs; report median and min plateau busbw and
8 B latency spread.

**L3 — two or more nodes (reserved window).**

```bash
mpirun -np 16 -N 8 --hostfile hosts.txt --bind-to numa -x NCCL_DEBUG=INFO -x NCCL_DEBUG_SUBSYS=INIT,NET \
       ./build/all_reduce_perf -b 8 -e 8G -f 2 -g 1 > l3_2node_run1.log 2> l3_2node_info.log
# rail-pinned, one GPU per node (DP-group shape), e.g. rail 3:
mpirun -np 8 -N 1 --hostfile hosts8.txt -x CUDA_VISIBLE_DEVICES=3 -x NCCL_IB_HCA=mlx5_3 \
       ./build/all_reduce_perf -b 8 -e 8G -f 2 -g 1 > l3_rail3.log
# per-rail RDMA sanity (perftest): server `ib_write_bw -d mlx5_3 -x <gid> --report_gbits`, then client:
ib_write_bw -d mlx5_3 -x <gid> --report_gbits -s 1048576 -D 10 <server>
```

The device name, GID index, and interface names are site-specific `[VENDOR-SPEC, 2026-10]`. Record in
a copy of `manifest.yaml` (extension `L3`) every field listed there, run ≥ 5 launches per
configuration, and state whether the fabric was idle.

> **Safety:** Large-message nccl-tests saturate the rails they use. Run only on reserved or drained
> nodes, never alongside production jobs that share rails or spines.

## 9. Intentionally flawed inputs

Two configurations contain planted problems with different signatures, and the "Avg bus bandwidth"
trailer is a trap in every file. Instructor notes are in `../solutions/lab/README.md`.
