# Lab 4 — Annotated Execution Trace: Diagnose a Training Step from a Profiler Capture

*Chapter 4 · Progressive Lab 4 (GPU baseline), part 1 · Tier **L1** (laptop) with an **L2** extension*

## 1. Goal and the real-world task it mirrors

A training job on an ORION HX8 node runs at 85 ms per step against an expected ≈ 60 ms, while
nvidia-smi reports the GPU 90–100 % "utilized". You are handed a two-step profiler capture exported to
CSV — the same tables you get from `nsys stats --report cuda_gpu_trace,cuda_api_trace` plus NVTX ranges
and per-kernel counters — and asked the question every GPU performance engineer is asked weekly:
**where is the time going, what is each problem worth, and what should we fix first?**

You will build a small, reusable trace-analysis module that computes GPU busy fractions, copy/compute
overlap, idle gaps attributed to their causes, copy bandwidths, theoretical occupancy and per-kernel
fraction-of-roof, and then turns them into ranked findings with estimated savings. The capture contains
several deliberately planted problems; part of the task is not flagging things that only look like problems.

## 2. Tier and realism boundary

- **L1 (required):** pure Python on a laptop; the data is `[SIMULATED]` by a seeded generator (instructor copy only;
  seed 4) — a discrete-event model of one CPU launch thread and two CUDA streams.
- **L2 (optional):** capture the same tables from your own GPU job (Section 8).

> **Realism boundary:** The simulated capture has the structure of a real export (correlation IDs,
> CPU-side NVTX ranges, memory kinds, launch configurations) but not its noise: no clock variation, no
> driver back-pressure, no PCIe contention, no multi-process interference. Occupancy computed here is
> *theoretical*; achieved occupancy and true DRAM bytes need Nsight Compute on real hardware.

## 3. Setup

```bash
cd book/part-2-accelerated-compute/ch04-gpu-architecture-cuda-execution/lab
python -m pip install -r ../../../../requirements.txt     # numpy, pandas (Python >= 3.10)
python check.py                                            # progress meter: TODO/FAIL per function
```

Files:

| Path | Content |
|---|---|
| `data/gpu_trace.csv` | One row per GPU activity: `kind` (kernel/memcpy), `name`, `stream`, `start_ns`, `end_ns`, `correlation_id`, `copy_kind` (HtoD/DtoH), `src_mem`/`dst_mem` (pageable/pinned/device), `bytes`, launch config (`grid_x`, `block_x`, `regs_per_thread`, `smem_per_block_bytes`), counters (`flop`, `dram_bytes`) |
| `data/cuda_api_trace.csv` | CPU-side CUDA API calls: `correlation_id`, `name`, `start_ns`, `end_ns`, `thread_id` |
| `data/nvtx_ranges.csv` | CPU-side NVTX ranges (`train_step_41`, `forward`, `backward`, `bwd_layer_N`, `debug_grad_norm_hook`, `optimizer_step`, …) |
| `data/device.json` | Occupancy limits (CC 9.0 class), peak BF16 FLOP/s and HBM bandwidth |
| `starter/trace_analysis.py` | The module you complete |
| `check.py` | Automated checks |

## 4. Background you need

- Manuscript Section 4.5 (launch overhead), 4.6 (streams, synchronization, pinned vs pageable),
  4.7 (occupancy calculation — Table 4.3 is your test oracle), 4.10 (NVTX is CPU-side; correlation IDs),
  4.11 (gap-attribution rule) and 4.12 (worked example — the same data).

## 5. Tasks

Implement the functions in `starter/trace_analysis.py` (each has a docstring with the exact contract).

1. **Interval arithmetic and utilization** — `merge_intervals`, `busy_ns`, `step_windows`,
   `utilization`, `copy_compute_overlap`. *Acceptance:* for `train_step_41`, busy(any) ≈ 89 %,
   busy(kernel) ≈ 79 %, copy overlap ≈ 13 %. Explain in one sentence why busy(any) is not "efficiency".
2. **Idle gaps with causes** — `find_gaps`. *Acceptance:* 15 `host_sync` gaps and ≈ 600 `launch_bound`
   gaps per step, and exactly one `dependency` gap per step (find the API calls that cause it). Identify which source-code construct produces each `host_sync`
   gap (use the NVTX ranges around them).
3. **Copies** — `copy_table`. *Acceptance:* four large pageable copies at ≈ 9–12 GB/s, two pinned at
   ≈ 48 GB/s. State why the pinned bandwidth rules out a degraded PCIe link.
4. **Occupancy** — `theoretical_occupancy`. *Acceptance:* reproduces Table 4.3 and the checker's seven
   cases, including the limiter and the warp-allocation granularity.
5. **Kernel summary** — `kernel_summary`. *Acceptance:* GEMMs compute-bound at ≈ 62 % of roof;
   `layernorm_bwd_fused_kernel` memory-bound at ≈ 22 %.
6. **Findings** — `analyze` (and the provided `render_report`). *Acceptance:* exactly the five finding
   codes, `LOW_OCCUPANCY` naming only the kernel that is both low-occupancy *and* far from its roof,
   savings in ms/step.
7. **Annotated analysis (written deliverable, `analysis.md`, ≤ 2 pages):** an annotated execution trace
   for one step — a timeline sketch (ASCII or Mermaid) marking the copy phase, forward, the sync gaps,
   backward with the side-stream prefetch, and the optimizer comb — plus the ranked findings table, a
   projected step time with arithmetic, the order in which you would fix things and why, how you would
   validate each fix, and what in this capture you could *not* conclude without real hardware.

## 6. Running the checker

```bash
python check.py                    # your implementation (starter/)
python check.py --impl solution    # instructor reference (removed from the student release)
python starter/trace_analysis.py --out report.md    # once implemented: writes the findings report
```

Each check prints `PASS`, `FAIL` (with the reason) or `TODO`. The exit code is 0 only when all pass.

## 7. Deliverable and grading rubric (100 points)

| Item | Points | Full marks when |
|---|---|---|
| Task 1 — utilization and overlap | 15 | Checks pass; busy(any) vs kernel vs efficiency explained correctly |
| Task 2 — gap attribution | 20 | Checks pass; each `host_sync` gap tied to its source construct (`.item()`, pageable copy) |
| Task 3 — copy table | 10 | Checks pass; PCIe-degradation hypothesis explicitly ruled out with evidence |
| Task 4 — occupancy | 10 | Checks pass; one configuration worked by hand in `analysis.md` |
| Task 5 — kernel summary | 10 | Checks pass; GEMM low occupancy correctly judged "by design" |
| Task 6 — findings and report | 15 | Checks pass; savings per step with units; report generated |
| Task 7 — annotated analysis | 20 | Timeline annotated; fixes ordered by evidence; projected step time with arithmetic; validation plan uses repeated runs; limitations stated |

## 8. Extension (L2): capture and analyse your own trace

Run on a single-GPU development machine you control — never on a shared production node.

```bash
# 1. Record the environment (copy manifest.yaml to manifest.l2.yaml and fill in the `record` fields).
nvidia-smi --query-gpu=name,vbios_version,driver_version,clocks.sm,clocks.mem --format=csv
nvcc --version; nsys --version; ncu --version; python -c "import torch; print(torch.__version__, torch.version.cuda)"
lspci -vvv -s "$(nvidia-smi --query-gpu=pci.bus_id --format=csv,noheader | head -1 | sed 's/^0000//')" | grep -E 'LnkCap|LnkSta'

# 2. Add NVTX ranges and torch.cuda.profiler.start()/stop() around two steps after warm-up
#    (manuscript Section 4.10), then capture:
nsys profile -t cuda,nvtx,osrt -s none --capture-range=cudaProfilerApi --capture-range-end=stop \
     -o mystep python train.py

# 3. Export tables (report names are version-sensitive: `nsys stats --help-reports` lists yours).
nsys stats --report cuda_gpu_trace,cuda_api_trace,nvtx_pushpop_trace --format csv --output mystep mystep.nsys-rep

# 4. Per-kernel counters for the top kernels (development node only; ncu replays kernels):
ncu --section SpeedOfLight --section Occupancy --section LaunchStats -k regex:<kernel_name> -c 5 \
    --csv python train.py > ncu_top.csv
```

Write a small adapter that maps the exported column names (for example `Start (ns)`, `Duration (ns)`,
`CorrId`, `Strm`, `GrdX`, `BlkX`, `Reg/Trd`, `SrcMemKd`, `DstMemKd`, `Bytes` — verify against your nsys
version) onto this lab's schema; FLOP and DRAM-byte counters can be replaced by ncu's SpeedOfLight
percentages. Run `analyze()` on three separate captures and report the spread of each metric. Label every
number `[MEASURED]` with the manifest attached. Try one fix (for example `pin_memory=True`) and show
before/after with the Chapter 6 benchmark protocol.

## 9. Intentionally flawed inputs

The capture contains planted problems and at least one planted distractor. Their list, magnitudes and
the reasoning they are meant to exercise are documented for instructors in
`../solutions/exercises-key.md` (section "Lab 4 — planted anomalies"). Do not look before submitting.
