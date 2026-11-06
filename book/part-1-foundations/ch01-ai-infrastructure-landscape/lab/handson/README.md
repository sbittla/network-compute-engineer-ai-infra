# Hands-on lab (Chapter 1): your GPU against its ceilings

## 1. What you will do

You will put a real GPU through the ceiling model of Section 1.6. First you measure its two ceilings, a
large BF16 matrix multiply (compute) and a device-to-device copy (memory bandwidth), and compare them with
the vendor-class peak *at the clock the GPU actually ran*. Then you sweep a matrix-vector product from
decode-like (batch 1) to GEMM-like (batch 4,096) and watch the dominant bound flip at the machine balance.
Finally you train a small transformer for a few hundred steps, measure tokens/s, achieved FLOP/s and MFU,
and classify the step as compute- or memory-bound with the evidence Table 1.7 asks for.

## 2. What is real here, and what is not

**Real:** every time, rate and clock in the evidence. The kernels are cuBLAS and PyTorch running on the
GPU; the step is a full forward, backward and fused-AdamW update of a 63-million-parameter decoder; power,
SM clock and clock-event reasons come from `nvidia-smi` sampled at about 100 ms during each measurement.

**Modeled:** the peak FLOP/s (SM count × FLOP per clock per SM × measured SM clock, with the per-SM
constant taken from NVIDIA's published peaks), the theoretical bandwidth (bus width × data rate), the
6*N* FLOP count, and the step's minimum memory traffic. The minimum traffic is 36 bytes per parameter for
weights, gradients and Adam state, plus twice the bytes PyTorch saves for backward. Those saved bytes
are measured with `saved_tensors_hooks`. The ceiling model's verdict is therefore `[MODELED]`; the
scaling test that confirms it is `[MEASURED]`.

**What one laptop GPU cannot show:** the communication and I/O bounds (`T_scaleup`, `T_scaleout`, `T_io`)
of Equation block 1.1. There is one GPU, no NVLink, no NIC in the path and no shared file system.
There is no HBM and no DCGM either, so `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE` and `DCGM_FI_PROF_DRAM_ACTIVE` are
not available and we confirm the class by scaling instead. WSL2 hides the PCIe tree as well. An RTX 4060
Laptop is about 35 times slower than an `HX8` GPU at BF16 and has a machine balance near 110 FLOP/B rather
than 295. **Ratios and mechanisms carry over; absolute values do not.** The decode-is-memory-bound result,
the crossover at the machine balance, and the gap between a GEMM's efficiency and a training step's MFU
all transfer. Tokens/s and TFLOP/s do not. The chapter's Level 3 extension (lab/README.md §8) does
the same on `HX8`-class nodes with DCGM profiling fields and multi-node traffic.

## 3. Requirements

| Item | Need |
|---|---|
| GPU | Yes. NVIDIA, Ampere or newer (BF16), at least 4 GB free. Tested on an RTX 4060 Laptop (8 GB). |
| Docker | No |
| Root | No |
| Disk | About 3 GB for the shared PyTorch environment (once); under 1 MB of results |
| RAM | 2 GB |
| Time | Setup 5 min the first time (PyTorch download), then about 1 min; run about 1.5 min plus any wait for the GPU lock |

## 4. Safety

The lab only runs its own processes on the GPU. It does not change clocks, power limits, persistence mode or
any host setting, and it reads `nvidia-smi` without writing to it. `run.sh` holds the shared GPU lock
(`/tmp/handson-gpu.lock`) for the whole measurement, so another lab's job cannot distort the numbers, and
`teardown.sh` kills a leftover `nvidia-smi` sampler if a run is interrupted.

## 5. Setup

```bash
cd book/part-1-foundations/ch01-ai-infrastructure-landscape/lab/handson
bash setup.sh          # checks nvidia-smi, creates ~/.venvs/ai-infra-handson (torch 2.5.1+cu124), prints versions
```

From the repository root on Windows, `python scripts/handson.py setup ch01` does the same inside WSL.

## 6. Steps

Run everything at once with `bash run.sh my-run` (results in `results/my-run/`), then read the outputs step by
step below. `CH01_QUICK=1 bash run.sh smoke` is a 40-second smoke test, too short for evidence. Write your
answers in `results/my-run/answers.md`.

### Step 1: inventory and the clock you will divide by

```bash
nvidia-smi -q -d CLOCK,POWER,PERFORMANCE      # also saved as nvidia_smi_q_before.txt
cat results/my-run/gpu_inventory.json         # SMs, compute capability, which nvidia-smi fields work here
```

Look for the maximum SM clock (`clocks.max.sm`), the enforced power limit, and the fields marked
`UNAVAILABLE` (on WSL2: `power.limit`, `fan.speed`, `temperature.memory`). The peak at the maximum clock is
SMs × 512 BF16 FLOP per clock per SM × maximum clock (Ada GeForce with FP32 accumulation, `[VENDOR-SPEC, 2026-10]`).

**Question 1.** Your GPU never runs at `clocks.max.sm` under a heavy load. What clock should "peak FLOP/s"
use when you compute MFU, and what happens to a reported MFU if a vendor's maximum boost clock is used instead?

### Step 2: the two empirical ceilings

`ch01_ceilings.py` runs back-to-back 8192³ BF16 GEMMs for 6 s, then 1 GiB device-to-device copies for 6 s.
In `report.md` (Step 2) compare:

- GEMM TFLOP/s against the clock-adjusted peak *and* the max-clock peak;
- copy GB/s against the theoretical 128-bit × 16 Gb/s = 256 GB/s;
- the SM clock and power in each segment (`summary.json` → `gemm.telemetry`, `copy.telemetry`).

**Question 2.** The GEMM reaches about 0.98 of the clock-adjusted peak, which falls in the "recheck" band of
Figure 1.5. What did you check to convince yourself the number is real, and why does the SM clock differ
between the GEMM and the copy?

### Step 3: from decode to GEMM, across the machine balance

`Y = X·W` with `W` an 8192 × 8192 BF16 matrix (128 MiB, four times the L2 cache) and batch `B` from 1 to
4,096. The intensity is about `B` FLOP/B, the same algebra as the decode example in Section 1.6.

```bash
column -s, -t results/my-run/gemv_sweep.csv   # raw: iterations and elapsed time per batch
```

In `report.md`, find the batch at which the dominant bound changes from memory to compute, and compare it
with the machine balance (clock-adjusted peak ÷ theoretical bandwidth).

**Question 3.** At `B = 1` the observed time is almost exactly `T_memory`. Using your numbers, how many
sequences would a decode batch need before this GPU stops being memory-bound, and why is the answer
different for an `HX8`?

### Step 4: a training step, its MFU and its class

A decoder with 8 layers, `d = 768`, 12 heads, vocabulary 8,192 and sequence 512, trained with BF16 autocast
and fused AdamW at batch 1, 4 and 16 (5 warm-up steps, then at least 6 s of timed steps each).

```bash
column -s, -t results/my-run/train_steps.csv | head   # every timed step
cat results/my-run/train_model.json                     # parameter count, 6N, saved-activation bytes
```

In `report.md` read tokens/s, achieved FLOP/s (6*N* per token), MFU against the clock-adjusted and
max-clock peaks, the two lower bounds and the ceiling fraction for each batch.

**Question 4.** Batch 16 has a ceiling fraction near 0.5, in the "meaningful" band. Where does the other half of
the time go, given that the GEMM alone reaches about 0.98? Name two costs the 6*N* model leaves out.

### Step 5: confirm the class with evidence, not the model

Table 1.7 says compute-bound work "scales with FLOPs when you change batch". The verdict section compares
step time when tokens per step grow four-fold (batch 4 → 16).

**Question 5.** Time per token changed by the ratio in the verdict. Does that confirm compute-bound? What
would the same ratio look like if the step were dominated by launch overhead, or by optimizer-state traffic?

## 7. Check your results

```bash
python check.py results/my-run
```

It re-derives the headline numbers from the raw files and tests physical sense. A GEMM above the
clock-adjusted peak, a copy above theoretical bandwidth, an MFU above the GEMM's efficiency, a decode-like
GEMV classified compute-bound, or a "compute-bound" verdict whose step time does not scale with FLOPs all
FAIL with a message. From the repository root: `python scripts/handson.py check ch01 my-run`.

## 8. Reference results

Measured on the reference machine (RTX 4060 Laptop, 80 W limit, WSL2). The bundle is in
[results/wsl2-rtx4060-laptop/](results/wsl2-rtx4060-laptop/), with the summary in its `report.md`.

| Measurement | Reference value | Source |
|---|---|---|
| BF16 GEMM 8192³ | 27.8 TFLOP/s at a mean SM clock of 2307 MHz and 80.2 W, power cap active in 100 % of samples | `ceiling_gemm.json`, telemetry `[MEASURED]` |
| Fraction of peak | 0.98 of the clock-adjusted peak (28.3 TFLOP/s); 0.73 of the max-clock peak (38.2 TFLOP/s) | `[MODELED]` peak |
| Device-to-device copy (1 GiB) | 228 GB/s = 0.89 of 256 GB/s, at SM 2535 MHz and 53.0 W | `ceiling_copy.json` `[MEASURED]` |
| Machine balance | 111 FLOP/B at the GEMM's clock `[MODELED]`; 122 FLOP/B empirical (GEMM ÷ copy) `[MEASURED]` | |
| GEMV sweep, B = 1 | 544 µs per call, 247 GB/s, memory-bound at 0.96 of `T_memory` | `gemv_sweep.csv` `[MEASURED]` |
| Bound changes | memory-bound up to B = 64, compute-bound from B = 256, around the 111 FLOP/B balance | `[MEASURED]` times, `[MODELED]` bounds |
| Training, batch 1 / 4 / 16 | 18,288 / 36,284 / 41,660 tokens/s; median steps 28.0 / 56.4 / 196.6 ms | `train_steps.csv` `[MEASURED]` |
| MFU, batch 16 | 0.55 clock-adjusted (15.7 TFLOP/s at 2314 MHz); 0.41 against the max-clock peak | 6*N* FLOPs `[MODELED]` |
| Verdict | batch 16 compute-bound, ceiling fraction 0.55; tokens ×4 gave step time ×3.48, time per token ×0.87 | `[MEASURED]` scaling |
| Idle | 18.4 W at SM 2250 MHz | telemetry `[MEASURED]` |

**Sense check against the published specs.** NVIDIA lists the RTX 4060 Laptop with 3,072 CUDA cores
(24 SMs), a boost clock of 1,470–2,370 MHz depending on the laptop's power setting, 8 GB of GDDR6 on a
128-bit bus at 16 Gb/s (256 GB/s), and a 35–115 W TGP range `[VENDOR-SPEC, 2026-10]`.

- *Clock.* `nvidia-smi` reports a maximum SM clock of 3105 MHz. That is the top of the VBIOS clock table,
  not the advertised boost, and the GPU never reaches it under load. Under the GEMM it settled at 2307 MHz,
  just under the 2,370 MHz top of the published boost range, because this laptop enforces an 80 W limit
  and the GEMM hit it. That is why the max-clock peak (38.2 TFLOP/s) makes the GEMM look like 0.73 of
  peak when it is really 0.98 of what the chip could do at the clock it ran.
- *Compute.* Ada GeForce runs BF16 with FP32 accumulation at 512 FLOP per clock per SM. That is NVIDIA's
  RTX 4090 figure of 165 TFLOP/s ÷ (128 SMs × 2.52 GHz). At the 2,370 MHz published boost this GPU's peak
  would be 29.1 TFLOP/s. The measured 27.8 TFLOP/s is 0.96 of that, which is typical for a large cuBLAS GEMM.
- *Memory.* The copy reaches 0.89 of 256 GB/s and the read-only GEMV at B = 1 reaches 0.96. A copy reads
  and writes, and the bus loses time turning around between the two. GDDR6 refresh costs a few percent
  more. The B = 1 GEMV only reads (128 MiB of weights, four times the 32 MB L2), so it gets closer to the
  pin rate. Neither exceeds it.
- *Training.* MFU 0.55 against a 0.98 GEMM ceiling. The rest of the step time goes to attention softmax,
  layer norms, the optimizer and kernel launches, which the 6*N* count leaves out. Compute-bound decoder
  training on data-center GPUs usually runs at 0.35–0.55 MFU, so this result is in range.

Other GPUs will give different numbers. The check tests physical sense, not equality with these.

## 9. Clean up

```bash
bash teardown.sh       # stops a leftover sampler or benchmark; the lab changes nothing else
rm -rf results/my-run  # if you do not want to keep your bundle
```

## Troubleshooting

- **`ERROR: no NVIDIA GPU visible (nvidia-smi failed)`** → install the NVIDIA driver (on WSL2, the Windows
  driver). On WSL2 `nvidia-smi` lives in `/usr/lib/wsl/lib`; the scripts add it to `PATH`, so start them
  with `bash setup.sh` / `bash run.sh` rather than calling the Python files directly.
- **First `setup.sh` is slow or fails in `pip`** → it builds the shared venv `~/.venvs/ai-infra-handson` and
  downloads PyTorch 2.5.1+cu124, so it needs network access. If `python3 -m venv` fails, install
  `python3-venv` (`sudo apt-get install python3-venv`). After a broken install, delete the venv and re-run.
- **The run stops with no output before a GPU step** → it is waiting for the shared GPU lock
  `/tmp/handson-gpu.lock`, held by another hands-on run. Let that run finish; `pgrep -fa flock` shows it.
- **`check.py` prints its usage text and exits 2** → pass the run folder: `python3 check.py results/<run-id>`.
- **Numbers from a `CH01_QUICK=1` run look noisy** → its measurement windows are shortened for a smoke test; submit a full `bash run.sh <run-id>` as evidence.

## 10. Connect to the chapter

- **Section 1.6** (ceiling model, ceiling fraction bands, machine balance, decode intensity): Steps 2–4.
- **Table 1.7** (what confirms each class): Step 5, where scaling replaces DCGM profiling fields.
- **Section 1.9** (W-TRAIN is compute-bound at 0.40 of peak): your step's MFU and ceiling fraction are the
  same quantities on one GPU.
- **Section 1.7** (goodput, the cost of a point of MFU): the gap you measured in Question 4 is the "busy but
  inefficient" loss.
- Chapter 6 develops the measurement discipline (warm-up, A/A noise, clock telemetry) used here only in
  outline; Chapter 2's hands-on lab explains why the SM clock moves.
