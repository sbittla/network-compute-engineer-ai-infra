# Hands-on lab (Chapter 2): power, clocks and throttling

## 1. What you will do

You will drive a real GPU through the phases a training node goes through: idle, a memory-bound phase, a
compute-bound phase, a cooldown, a load ramp, and a square wave of 1 s compute and 1 s idle like a
synchronous training step. Throughout, you record power, SM clock, temperature and the clock-event
reasons at 100 ms. From that record you find where the power limit binds, what it costs in clock, and how
large and fast the step-boundary swing of Table 2.5 is on one GPU.

## 2. What is real here, and what is not

**Real:** board power, SM and memory clocks, temperature, utilization and the clock-event reason bitmask,
as the driver reports them through `nvidia-smi --query-gpu=... -lms 100`. The violation counters
(`clocks_event_reasons_counters.*`) are real too, read at every phase boundary. So are the power limit the
GPU enforces and the refusal you get when you try to change it.

**What this platform does not report** (recorded in `field_availability.json`): on WSL2 with an RTX 4060
Laptop, `power.limit` (the requested limit), `fan.speed` and `temperature.memory` read `[N/A]`. Applications
clocks are deprecated. Power-limit changes are refused with "Insufficient Permissions" and clock locking
(`-lgc`) fails, because the Windows driver owns these settings. The violation counters do not agree with the
flags on this platform (see Step 4), so treat them as a lesson in checking a counter before trusting it.
There is no DCGM, so the `DCGM_FI_DEV_*` fields of Section 2.6 are not available; the `nvidia-smi` fields
are the same NVML values underneath.

**What one GPU cannot show:** node power (CPUs, NICs, fans, PSU losses; Table 2.2), rack and row
aggregation, breaker trip curves, UPS and generator behaviour, and 256 GPUs swinging together. The
achieved sample interval is about 100 ms, so the millisecond excursions in the first row of Table 2.5 are
invisible and the edges of the square wave fall within one sample. A laptop's 80 W limit and its cooling are
not a 700 W `HX8` GPU's. **Ratios and mechanisms carry over; absolute values do not.** The order idle <
memory-bound < compute-bound, the compute phase pinned at the limit with the clock reduced, and the size of
the step swing relative to the peak all transfer to a data-center GPU. The watts do not. The chapter's L2
extension (lab/README.md §8) measures a whole server through its BMC, and L3 a rack and CDU.

## 3. Requirements

| Item | Need |
|---|---|
| GPU | Yes. Any NVIDIA GPU with BF16 (Ampere or newer) and about 1.5 GB free. Tested on an RTX 4060 Laptop (8 GB). |
| Docker | No |
| Root | No (the lab never changes limits or clocks) |
| Disk | The shared PyTorch environment (about 3 GB, once); under 1 MB of results |
| RAM | 2 GB |
| Time | Setup about 1 min after the first time; run about 2.5 min plus any wait for the GPU lock |

## 4. Safety

The lab runs its own GEMMs and copies on the GPU and reads `nvidia-smi`. It changes no clock, power limit
or host setting. The one write it attempts is `nvidia-smi -pl <current limit>`, which sets the limit to the
value it already has: a no-op where it is allowed, and a recorded refusal where it is not. Where you *are*
allowed to cap power (root on bare-metal Linux), do it only on a dedicated machine you own, as the Safety
box in Section 2.6 says, and restore the default afterwards. `run.sh` holds the shared GPU lock for the
whole run, and `teardown.sh` stops a leftover sampler. The GPU will reach its normal hot-load temperature
(about 80–87 °C on a laptop), the same as in any game or training run.

## 5. Setup

```bash
cd book/part-1-foundations/ch02-anatomy-of-an-ai-data-center/lab/handson
bash setup.sh
```

From the repository root on Windows: `python scripts/handson.py setup ch02`.

## 6. Steps

`bash run.sh my-run` runs all phases unattended (about 2.5 min) and writes `results/my-run/`.
`CH02_QUICK=1 bash run.sh smoke` is a shorter smoke test. Then work through the evidence below and write your
answers in `results/my-run/answers.md`.

### Step 1: what the driver will and will not tell you

```bash
nvidia-smi -q -d POWER,PERFORMANCE                 # saved as nvidia_smi_q_before.txt
cat results/my-run/field_availability.json         # every field the lab asked for, and which are UNAVAILABLE
cat results/my-run/power_controls.txt              # the -pl attempt and its answer
```

Note the enforced, default, minimum and maximum power limits, and which fields are unavailable.

**Question 1.** The laptop reports a default limit of 80 W but a maximum of 120 W. Which one did the GPU
enforce during the run, and what does the refused `-pl` tell you about who controls power policy on this
machine compared with the `HX8` in Section 2.6?

### Step 2: idle and the memory-bound phase

The first 10 s are idle, then 25 s of 1 GiB device copies. In `report.md` compare the two rows: power,
SM clock, memory clock, temperature and the reasons seen.

**Question 2.** The copy loop keeps the GPU 100 % "utilized", yet it draws well under the limit and runs at
the highest SM clock in the whole run. Why does a memory-bound phase use less power than a compute-bound
one, and what does that predict for inference decode on an `HX8`?

### Step 3: the compute-bound phase, where the limit binds

25 s of back-to-back 8192³ BF16 GEMMs.

```bash
grep -c '0x0000000000000004$' results/my-run/ch02_telemetry.csv   # samples whose only reason is SW Power Cap
```

Compare the compute row with the memory row: power against the limit, SW Power Cap share, SM clock, and
temperature rise.

**Question 3.** The compute phase asks for more work per clock than the copy, yet its SM clock is *lower*.
Explain this with the decision table in "Throttling: how power and heat show up as clocks". Is it a
problem on this machine?

### Step 4: two ways to count throttling

Section 2.6 says to take the difference of the cumulative violation counters across a window.
`counters.json` holds them at every phase boundary; `report.md` shows the counter's power-capped share of
each phase next to the share of samples carrying the SW Power Cap flag.

**Question 4.** Do the counter and the flag agree for the compute phase? If they do not, which do you
believe, and what would you check on a data-center GPU before alerting on `DCGM_FI_DEV_POWER_VIOLATION`?

### Step 5: the ramp, and where the limit starts to bind

GEMMs in 50 ms periods at 25, 50, 75 and 100 % duty, 8 s each. `report.md` gives the mean power, p95
power, mean SM clock and SW Power Cap share per level, and the lowest duty at which the limit binds.
Also look at the P-state and SM clock at 25 % duty in `ch02_telemetry.csv`: if the cooldown let the GPU
reach P8, the driver may keep a light load at a low clock (see Reference results).

**Question 5.** At which duty does the limit start to bind? At that level the p95 power can exceed the
limit while the mean stays under it. What does that say about the averaging window of a power limit, and
about what a power cap does *not* protect in Table 2.5?

### Step 6: the step-boundary swing

Eight cycles of 1 s compute and 1 s idle, the pattern of a synchronous training step whose communication is
not overlapped. `report.md` gives the high and low plateaus, the swing, low/high, and the 10–90 % rise as
resolved by the sampler.

**Question 6.** Scale your measured swing to ORION. If every `HX8` GPU swung between your measured low/high
ratio of its 700 W peak in step, what would the per-node and 32-node AC swing be (use 0.94 PSU efficiency,
as Section 2.6 does)? Why can a 100 ms sampler not tell you whether the PDU sees a step or a ramp?

## 7. Check your results

```bash
python check.py results/my-run
```

It re-derives the per-phase power from the raw telemetry and tests physical sense. It checks that idle <
memory < compute power, that compute p95 power is within 15 % of the enforced limit, and that a SW Power Cap
flag only appears near the limit. Where the cap binds in compute but not in memory, the capped clock must be
lower. Ramp power must rise with duty, the square wave must swing, and the cumulative counters must never go
backwards. From the repository root: `python scripts/handson.py check ch02 my-run`.

## 8. Reference results

Measured on the reference machine (RTX 4060 Laptop, 80 W enforced limit, WSL2). The bundle is in
[results/wsl2-rtx4060-laptop/](results/wsl2-rtx4060-laptop/).

| Measurement | Reference value | Source |
|---|---|---|
| Power limit | 80 W enforced (default 80 W, range 5–120 W); `nvidia-smi -pl 80.00` refused with "Insufficient Permissions" (exit 4) | `nvidia_smi_q_before.txt`, `power_controls.txt` |
| Unavailable fields | `power.limit`, `fan.speed`, `temperature.memory` | `field_availability.json` |
| Sampling | 1,119 samples, median interval 110 ms (p95 137 ms) against 100 ms requested | `ch02_telemetry.csv` `[MEASURED]` |
| Idle | 7.6 W, SM 375 MHz, memory 810 MHz (the GPU drops to P5/P8) | `[MEASURED]` |
| Memory-bound (1 GiB copies) | 53.6 W = 0.67 of the limit, SM 2535 MHz, SW Power Cap in 0 % of samples | `[MEASURED]` |
| Compute-bound (8192³ BF16 GEMM) | 80.0 W = 1.00 of the limit, SM 2250 MHz, SW Power Cap in 100 % of samples, 68 → 81 °C, no thermal slowdown | `[MEASURED]` |
| Cost of the cap | 285 MHz (11 %) less SM clock than the uncapped memory phase | `[MEASURED]` |
| Violation counter vs flag (compute) | counter says power-capped for 2.86 s of 25 s (11 %); the flag is set in 100 % of samples | `counters.json` `[MEASURED]` |
| Duty ramp 25 / 50 / 75 / 100 % | 9.9 / 61.4 / 73.5 / 79.8 W; SW Power Cap 0 / 25 / 98 / 100 %; the limit binds from 75 % | `[MEASURED]` |
| Square wave (1 s on, 1 s off, 8 cycles) | 23.4 W → 81.9 W, swing 58.5 W, low/high 0.29; the 10–90 % rise falls within one 0.11 s sample | `[MEASURED]` |

**The 25 % ramp point.** At 25 % duty the GPU drew 9.9 W at 585 MHz SM and 810 MHz memory, in P5. The
12 s cooldown before the ramp had let it drop to P8 (210 MHz). Utilization then read only 35–39 %, so the
driver's clock governor never raised it to P0. At 50 % duty it jumped to P0 within a second. The GEMM work
in each 12.5 ms window therefore ran about four times slower than at full clock. A shorter smoke run, whose
cooldown was 3.6 s, entered the 25 % level still in P0 and drew 34 W at 2163 MHz. Both are real. Light,
bursty load on a GPU is governed by its P-state policy as well as by the power limit. That matters for
low-load inference, where a "25 % busy" GPU may be running at a quarter of its clock.

**Sense check against the published specs.** NVIDIA lists the RTX 4060 Laptop with a 35–115 W TGP range
(the laptop maker picks the value) and a boost clock of 1,470–2,370 MHz `[VENDOR-SPEC, 2026-10]`.

- *Power.* This laptop enforces 80 W, inside that range. The compute phase sits exactly at it, with a
  p95 of 81.1 W, so the limit is enforced on a short average rather than on every sample. The driver
  reports a 120 W maximum, but the refused `-pl` shows that the Windows host driver, not the Linux guest,
  owns power policy.
- *Clock.* Capped at 80 W, the GEMM runs at 2250 MHz, just under the published 2,370 MHz top boost. The
  memory phase runs at 2535 MHz, above the published boost, because it is far from the power limit and the
  VBIOS clock table goes up to 3105 MHz. Memory stays at 8000 MHz (16 Gb/s GDDR6) under every load.
- *Temperature.* The compute phase peaks at 81 °C and SW Thermal Slowdown never appears, so the only
  throttle in this run is power.
- *The swing.* low/high = 0.29 here against ORION's 0.43 `[ILLUSTRATIVE]`. The laptop's idle half falls
  further because nothing else (no communication, no NIC traffic) keeps it busy, and its idle floor is only
  about 23 W one second after a GEMM.

Other GPUs will give different numbers. The check tests physical sense, not equality with these.

## 9. Clean up

```bash
bash teardown.sh       # stops a leftover sampler or phase driver; nothing else was changed
```

## 10. Connect to the chapter

- **Section 2.2** (where the watts go): the GPU board is the part you measured; Table 2.2 adds the rest of
  the node.
- **Section 2.6, Table 2.5** (power on three timescales): Step 6 is the middle row on one GPU; the first row
  is below the sampler's resolution.
- **Section 2.6, Power capping**: Steps 1 and 5. The limit is enforced on an average, and on this platform you
  cannot change it.
- **Section 2.6, Throttling**: Steps 3 and 4, the clock-event reasons as a decision table and the violation
  counters as differences.
- **Section 2.12** (the afternoon slowdown): the compute phase's capped clock is the single-GPU form of a
  facility constraint showing up as clocks.
- Chapter 21's hands-on lab turns the same telemetry into energy per unit of work and cost.
