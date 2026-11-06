# Ch 4 hands-on: profile a training step — `wsl2-rtx4060-laptop`

Every number below is `[MEASURED]` on the machine in `environment.json`; the step that produced it is named.

## Step 1 — the symptom

- Baseline step: median **39.80 ms** over 150 steps `[MEASURED, step 1]`.
- nvidia-smi GPU-Util while the job ran: median **87.0 %** (62 samples at 100 ms) `[MEASURED, step 1]`: a duty cycle, not efficiency.

## Step 2 — torch.profiler (CPU side)

| Variant | Kernel launches / step | Graph launches / step | Synchronize calls / step (step body, excl. end of step) | `_local_scalar_dense` / step | `nonzero` / step | `is_nonzero` / step | GPU (device) events recorded |
|---|---|---|---|---|---|---|---|
| baseline | 1010 | 0 | 12 | 86 | 8 | 4 | 0 |
| fixed | 956 | 0 | 0 | 82 | 0 | 0 | 0 |
| graphed | 3 | 1 | 0 | 0 | 0 | 0 | 0 |

`_local_scalar_dense` also counts host-memory reads: non-capturable AdamW reads each parameter's CPU-side step counter with `.item()`, which does not wait for the GPU. The synchronize count is the ground truth.

All `[MEASURED, step 2]`. A device-event count of 0 means CUPTI delivered no GPU activity to torch.profiler on this platform (WSL2); the GPU side comes from Nsight Systems below.

## Steps 3, 5, 6 — Nsight Systems timeline (median over the captured steps per variant)

| Variant | Step window (ms) | GPU busy (%) | Kernels / step | Synchronize calls / step | host_sync gaps (n, ms) | launch_bound gaps (n, ms) | dependency gaps (n, ms) |
|---|---|---|---|---|---|---|---|
| baseline | 63.42 | 54.2 | 1010 | 13 | 11.0, 0.90 | 352.5, 25.81 | 53.0, 1.20 |
| fixed | 46.29 | 72.2 | 956 | 2 | 0.0, 0.00 | 177.5, 10.80 | 20.5, 0.59 |
| graphed | 34.65 | 96.5 | 1048 | 2 | 0.0, 0.00 | 2.0, 0.37 | 3.0, 0.16 |

All `[MEASURED, steps 3/5/6]`; gaps ≥ 10 µs inside each `train_step_N` NVTX range, attributed with the Section 4.11 rule by `gaps.py`.

## Step 4 — which lines synchronize

`set_sync_debug_mode("warn")` printed **12** warnings for one step `[MEASURED, step 4]`, at these lines of `train_step.py`:

- line 94: `loss = per_token[mask].mean()                 # boolean indexing: data-dependent shape -> host sync`
- line 95: `if not torch.isfinite(loss):                  # Python branch on a GPU value -> host sync`

## Step 5 — the fix, re-measured (separate processes, interleaved)

| Variant | Runs | Run medians (ms) | Mean of run medians (ms) |
|---|---|---|---|
| baseline | 7 | 38.70, 39.55, 38.60, 39.14, 38.78, 39.69, 49.17 | 40.52 |
| fixed | 7 | 40.93, 35.96, 35.51, 36.31, 35.32, 35.61, 39.19 | 36.97 |
| graphed | 7 | 34.73, 34.87, 34.48, 34.91, 34.37, 34.36, 34.25 | 34.57 |

- fixed vs baseline: **-8.7 %** step time (1.10×), exact permutation p = 0.016 `[MEASURED, step 5]`

- graphed vs fixed: **-6.5 %** step time (1.07×), exact permutation p = 0.001 `[MEASURED, step 5]`

- graphed vs baseline: **-14.7 %** step time (1.17×), exact permutation p = 0.001 `[MEASURED, step 5]`

## Step 6 — CUDA Graphs

- Capturing the *baseline* step: failed, as it must — `FloatingPointError: non-finite loss` `[MEASURED, step 6]`.
- The fixed step captures; its timing is the `graphed` row above.
- Launch-bound regime (`--batch 4`, 4 interleaved runs each): fixed 30.16, 35.27, 37.03, 39.38 ms, graphed 21.03, 21.55, 21.10, 21.07 ms: **-40.3 %** (1.67×), exact permutation p = 0.029 `[MEASURED, step 6b]`.

