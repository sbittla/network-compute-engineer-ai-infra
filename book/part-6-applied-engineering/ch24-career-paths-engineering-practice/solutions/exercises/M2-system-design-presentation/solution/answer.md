# M2 — System-design interview presentation: marking notes and reference points

Scored out of 20 (key): assumptions 3 + arithmetic 5, diagram 3, failure domains 3, validation 2, follow-ups 2
+ rehearsal 2. Structure follows Sections 24.5–24.7.

**What the arithmetic must show (walk-through 1 baseline, Section 24.6, `[MODELED]`).** FLOP/step =
6 × 70e9 × 4,194,304 = 1.76 × 10¹⁸; GPUs for 20 s at 989 TFLOP/s and 40 % MFU = 222.6 → 256 GPUs, step 17.4 s;
state 16 B/param → 1.12 TB → TP × PP = 32 (TP = 8 in the node, PP = 4, DP = 8); TP traffic 1.20 TB per GPU per
step (3.3 s on NVLink vs 30 s on a NIC); DP 7.66 GB per GPU (0.19 s); checkpoint 980 GB / 80 GB/s = 12.25 s,
Young's τ ≈ 2,058 s; bubble 3/131 = 2.3 %.

**The changed constraint must propagate.** Example: sequence length 8,192 doubles the per-micro-batch
activation to 134 MB and the TP volume per micro-batch; with the global batch held at ≈ 4 M tokens the
micro-batch count halves (64), so TP bytes per step stay ≈ 1.2 TB but activation memory per GPU doubles and
must be re-checked (more recomputation, or PP = 8). For walk-through 2 (Section 24.7), a change to 2,048 GPUs
hits the two-tier ceiling k²/2 = 2,048 exactly: 64 leaves, 32 spines, one link per pair. A presentation that
changes the constraint but reuses the baseline numbers scores at most half the arithmetic marks.

**Diagram and failure domains.** A data-path diagram (TP on NVSwitch, DP/PP on NIC *r* → rail leaf *r*, as in
Figure 24.3) and a failure-domain table: GPU/node (job restart from checkpoint), rail leaf (every multi-node
job on that rail hangs), rack power (4 nodes, 32 GPUs), storage (checkpoint stall), each with its detection
signal.

**Validation and follow-ups.** Day one: per-node burn-in and topology check, per-rail `ib_write_bw`,
`all_reduce_perf` at 2, 4, …, 32 nodes against a baseline, a checkpoint write timing. Good anticipated
follow-ups: "Why buy non-blocking spines if rail-aligned traffic never crosses them?"; "What if MFU is 30 %?"
(step 17.4 × 40 / 30 = 23.2 s, above target: 1.76e18 / (20 s × 989e12 × 0.30) = 296.9 → at least 297
GPUs, i.e. 320 GPUs = 40 nodes to keep TP × PP = 32 and DP = 10, or renegotiate the target).

**Deductions.** Unlabelled numbers; no rehearsal time; diagram without directions or rates.
