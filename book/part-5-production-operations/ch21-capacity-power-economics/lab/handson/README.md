# Hands-on lab (Chapter 21): performance per watt

## 1. What you will do

You will run one fixed job, training a small transformer on 524,288 tokens, several times on a real GPU
while recording board power every 100 ms. Each time you change how hard the GPU works (batch size) or how
much of the time it waits for work (busy fraction). From the power record you compute the job's energy as
the integral of power over time, then energy per token and per FLOP. You then run Section 21.4's
cost-per-useful-GPU-hour ladder on *your* measured power, throughput and goodput, beside the book's
$3.00 per GPU-hour ORION figure, and explain why the two differ.

## 2. What is real here, and what is not

**Real:** the job's wall time, busy time and tokens, and the GPU board power, SM clock and SW Power Cap
flag behind every energy number. Two independent power readings, the instantaneous one integrated by the
lab and the driver's 1 s average, are cross-checked by `check.py`. Whether this platform lets you change the
power limit or lock clocks is real too: the lab asks the driver and records its answer.

**What you cannot vary here, and what you vary instead.** Section 21.8's lever is the power cap. On WSL2
the Windows driver owns it: `nvidia-smi -pl` is refused ("Insufficient Permissions") and `nvidia-smi -lgc`
fails, so the lab cannot sweep caps or clocks. It varies what you *can* control: **workload intensity**
(batch 1, 4, 16) and **duty cycle** (the same work with idle gaps, to 75 %, 50 % and 25 % busy). The GPU
still gives you one real point on the cap curve, because its firmware holds it at its 80 W limit
under full load (Chapter 2's hands-on lab). On bare-metal Linux with root, `CH21_ALLOW_POWER_CAP=1 bash
run.sh` also runs the job at 85 %, 70 % and 55 % of the current limit and restores it afterwards. That path
is untested on the reference machine, because WSL2 refuses it.

**Modeled or assumed:** FLOP counts (6*N* per token); every input in `cost_inputs.json`, such as purchase
price, electricity tariff, amortization and the share of hours you use the GPU (`[ASSUMPTION]`, edit them);
and ORION's figures, which are the chapter's `[MODELED]` values.

**What one laptop GPU cannot show:** node, rack and facility power. `nvidia-smi` measures the GPU board
only, not the CPU, memory, NICs, fans or PSU losses, nor PUE. The capex, staff, network and colocation
that make up most of ORION's $3.00 are absent too, as are a scheduler's allocation gaps and the failures
that set ORION's 0.88 goodput. **Ratios and mechanisms carry over; absolute values do not.** Fuller batches
cost less energy per unit of work, idle-but-allocated time raises energy and cost per unit, and cost per
useful hour is nominal cost divided by the ladder. These hold on any GPU. The dollars do not. The chapter's
L2 extension (`lab/l2/`) adds a GEMM-level perf/W model, and L3 uses PDU telemetry on a lab rack.

## 3. Requirements

| Item | Need |
|---|---|
| GPU | Yes. NVIDIA with BF16 (Ampere or newer), about 3 GB free. Tested on an RTX 4060 Laptop (8 GB). |
| Docker | No |
| Root | No. Root is needed only for the optional cap sweep on bare-metal Linux. |
| Disk | The shared PyTorch environment (about 3 GB, once); under 2 MB of results |
| RAM | 2 GB |
| Time | Setup about 1 min after the first time; run about 4 min plus any wait for the GPU lock |

## 4. Safety

By default the lab changes nothing on the host. It runs its own training job and reads `nvidia-smi`. To
test whether the power limit may be changed it sets the limit to the value it already has, which is a no-op
where allowed. The optional cap sweep (`CH21_ALLOW_POWER_CAP=1`) is for a dedicated machine you own. It
records the original limit in `results/.ch21_power_limit_changed` before changing anything, restores it at
the end of the run, and `teardown.sh` restores it if the run was interrupted. The optional clock-lock probe
(`CH21_PROBE_CLOCK_LOCK=1`) asks for the widest possible range and resets it straight away with `-rgc`. Do
not run either on a shared GPU. `run.sh` holds the shared GPU lock for the whole measurement.

## 5. Setup

```bash
cd book/part-5-production-operations/ch21-capacity-power-economics/lab/handson
bash setup.sh
$EDITOR cost_inputs.json     # optional now, and the analysis can be re-run later: your price, tariff and hours of use
```

From the repository root on Windows: `python scripts/handson.py setup ch21`.

## 6. Steps

`bash run.sh my-run` runs everything (about 4 min) and writes `results/my-run/`. To re-cost with new inputs
without re-measuring, run `python3 ch21_analyze.py results/my-run my_inputs.json`. The inputs a bundle was
costed with are stored in it as `cost_inputs.json`. Write your answers in `results/my-run/answers.md`.

### Step 1: which power controls do you have?

```bash
cat results/my-run/controls.txt      # current/default/min/max limit and the answer to `nvidia-smi -pl <same value>`
```

**Question 1.** Section 21.8's best lever is "the lightest cap that fits one more node". On this machine you
cannot set a cap. What does the GPU do instead under full load (look at the SW Power Cap column), and how
does that make it a single, fixed point on the throughput-versus-cap curve?

### Step 2: the same job at three intensities

Batches 1, 4 and 16 each train the same 524,288 tokens. In `report.md` compare average power, wall time,
energy, joules per token and TFLOP per joule.

**Question 2.** Batch 16 draws the most power yet uses the least energy for the job. Explain this with
energy = power × time and with what the GPU spends at batch 1 that does not scale with work.

### Step 3: the same job with idle gaps (goodput)

Batch 16 with a sleep after every step, giving 75 %, 50 % and 25 % busy. This is a data loader that cannot
keep up, a straggler, or a half-used allocation. Compare energy per token with the fully busy job.

**Question 3.** How much extra energy did the 25 %-busy job use for the same tokens, and where did it go? Why
does a lower *average* power here mean a *worse* performance per watt, the opposite of what a power cap does?

### Step 4: cost per useful GPU-hour, yours beside ORION's

`report.md` shows four things. First, the book's ladder ($3.00 nominal → $4.72 per useful GPU-hour).
Second, ORION's $3.00 with your measured goodput in place of 0.88. Third, your own nominal and useful
cost per GPU-hour, from `cost_inputs.json` and the measured power. Fourth, cost per million tokens and per
PFLOP for both.

**Question 4.** Your nominal GPU-hour costs a few cents; ORION's costs $3.00. List the three biggest reasons,
using Table 21.3, and say which of them would still apply if you rented one cloud GPU instead.

**Question 5.** Electricity is about 4 % of ORION's TCO. What share is it of your nominal hour? Which input
would you change in `cost_inputs.json` to make the two cases comparable, and does "power matters for
capacity far more than for cost" (Section 21.4) still hold for you?

### Step 5: energy per unit of work against ORION

Compare TFLOP per joule, not tokens per joule: a token of ORION's 70B model is about 1,100 times the work
of a token of this 63M model.

**Question 6.** ORION's W-TRAIN step works out to about 0.33 TFLOP/J of IT energy. Your batch-16 job achieves
the TFLOP/J in the report, measured at the GPU board. Name two things that make the comparison unfair in
each direction.

## 7. Check your results

```bash
python check.py results/my-run
```

It re-integrates every job's energy from the raw telemetry and checks it against the driver's own 1 s
average. Every job must do the same work, and power must stay under the limit and above half of idle. A
fuller batch must give more tokens per joule, and energy per token must rise as the busy fraction falls.
The ORION ladder must give $4.72, and cost per useful GPU-hour must rise as goodput falls. A cap sweep may
only appear where caps are allowed, and must leave the limit restored. From the repository root:
`python scripts/handson.py check ch21 my-run`.

## 8. Reference results

Measured on the reference machine (RTX 4060 Laptop, 80 W limit, WSL2), with the default `cost_inputs.json`.
The bundle is in [results/wsl2-rtx4060-laptop/](results/wsl2-rtx4060-laptop/).

Every job trained the same 524,288 tokens. Idle board power was 16.0 W. Power was sampled every 111 ms
(median, 1,362 samples), and the integrated power agrees with the driver's own 1 s average within 4 %.

| Job | Busy | Wall s | Avg power W | Energy kJ | mJ/token | TFLOP/J | SM clock MHz | at power cap |
|---|---:|---:|---:|---:|---:|---:|---:|---:|
| batch 1 | 1.00 | 28.5 | 69.2 | 1.97 | 3.75 | 0.101 | 2535 | 0 % |
| batch 4 | 1.00 | 14.3 | 78.6 | 1.12 | 2.14 | 0.177 | 2445 | 100 % |
| batch 16 | 1.00 | 12.2 | 79.3 | 0.97 | 1.85 | 0.205 | 2370 | 100 % |
| batch 16, 75 % busy | 0.75 | 16.3 | 68.4 | 1.12 | 2.13 | 0.177 | 2415 | 76 % |
| batch 16, 50 % busy | 0.50 | 24.3 | 52.7 | 1.28 | 2.44 | 0.155 | 2520 | 49 % |
| batch 16, 25 % busy | 0.25 | 48.4 | 37.0 | 1.79 | 3.42 | 0.111 | 2535 | 19 % |

All `[MEASURED]`, except TFLOP/J, which uses the modeled 6*N* FLOP per token.

**Power controls.** `nvidia-smi -pl 80.00`, which sets the limit to the value it already has, was refused
with "Insufficient Permissions". The 80 W limit belongs to the Windows driver, so there is no cap sweep.
The reference run did not probe clock locking, because the lab standard forbids changing clocks on a
shared GPU. A development run with `CH21_PROBE_CLOCK_LOCK=1` saw `-lgc` refused too. What the GPU does
instead shows in the last column: at batch 4 and 16 the SW Power Cap flag was set in every sample. The
firmware holds the board at its limit, 79 W against 80 W, and lowers the SM clock to stay there: 2,370 MHz
at batch 16 against 2,535 MHz at batch 1. This GPU is one fixed point on the throughput-against-cap curve.

**Intensity.** Batch 16 drew 15 % more power than batch 1 but finished in 43 % of the time, so it used
half the energy: 2.03× the tokens per joule. At batch 1 the GPU pays for clocks, memory and kernel
launches on every step, and the per-step work is too small to amortise them. A fuller batch spreads that
fixed cost over more tokens. Section 21.5's energy per useful unit of work rewards this, even though the
watts go up.

**Busy fraction.** At 25 % busy the same tokens cost 1.79 kJ instead of 0.97 kJ, 85 % more (75 %: +15 %;
50 %: +32 %). The extra energy is the idle-but-allocated time: 36 s spent near the 16 W idle floor while
nothing ran. Average power fell to 37 W, yet performance per watt got worse. A power cap lowers power and
keeps the work flowing, but idle gaps lower power and add time. Energy is power × time, so only the cap
helps.

**Cost** (default `cost_inputs.json`, `[ASSUMPTION]`: $1,500 over 3 years, $0.08/kWh, used 25 % of hours).

| Case | Nominal $/GPU-h | Goodput | $/useful GPU-h | Electricity share |
|---|---:|---:|---:|---:|
| ORION (Section 21.4) `[MODELED]` | 3.00 | 0.88 | 4.72 | 4 % |
| This laptop, batch 16 | 0.060 | 1.00 | 0.239 | 4 % |
| This laptop, 25 % busy | 0.059 | 0.25 | 0.942 | 3 % |

The ORION row reproduces the chapter's ladder exactly: $3.00 ÷ (0.85 × 0.85 × 0.88) = $4.72. Put the
measured goodput into ORION's rate and the useful hour costs $4.15 at full busy and $16.64 at 25 % busy.
That makes the point of Section 21.4: cost per useful hour is the nominal cost divided by every rung of the
ladder. Here the nominal hour costs 6 cents. It is almost all hardware amortisation: no staff, network,
colocation or facility, and only the GPU board's power. The useful hour costs 4× that, $0.239, because
this machine runs jobs only 25 % of its hours. Electricity is about 4 % of the nominal hour, close to
ORION's share, and only by coincidence: both are dominated by capital cost.

**Energy per FLOP.** Batch 16 reaches 0.205 TFLOP/J at the board, against ORION's 0.33 TFLOP/J at the
whole node's IT load `[MODELED]`. ORION's figure carries CPUs, NICs and fans that this one leaves out, but it
also runs at 40 % MFU on an H100-class GPU with far more FLOP per watt.

Other GPUs will give different numbers. The check tests physical sense, not equality with these.

## 9. Clean up

```bash
bash teardown.sh       # stops a leftover job or sampler; restores the power limit if a cap sweep was interrupted
```

## 10. Connect to the chapter

- **Section 21.1** (four definitions of utilization): Step 3's busy fraction is the goodput rung; your
  allocated fraction is an input.
- **Section 21.4** (TCO and the cost ladder): Step 4 reproduces $3.00 → $4.72 and runs the same ladder on
  your machine.
- **Section 21.5, Energy per useful unit of work**: Steps 2, 3 and 5. Track tokens per kWh and tokens per
  dollar; they reward different things.
- **Section 21.8** (power capping): Step 1. On WSL2 the cap is fixed by firmware; on a dedicated Linux host
  the opt-in sweep measures the curve the chapter calls illustrative.
- Chapter 2's hands-on lab shows the same GPU hitting its power limit phase by phase.
