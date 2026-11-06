# W2 — What a degraded node costs W-TRAIN

W-TRAIN on ORION: step 17.4 s at 40 % MFU, TP 8 × PP 4 × DP 8 = 256 GPUs (Section 16.6).

**(a) One GPU at 85 % throughput.** Only the compute share on the critical path stretches:
T = 0.7 × 17.4 / 0.85 + 0.3 × 17.4 = 14.33 + 5.22 = **19.55 s**.
Throughput loss = 1 − 17.4 / 19.55 = **11.0 %**.
GPU-equivalents lost = 256 × 0.110 = **28.1 GPUs** (three and a half nodes' worth) `[MODELED]`.
Wrong method: applying 0.85 to the whole step (17.4 / 0.85 = 20.47 s, 15 % loss).

**(b) One compute NIC on Gen5 x8.**
PCIe ceiling per direction: Gen5 x16 = 32 GT/s × 16 lanes × 128/130 / 8 = 63.0 GB/s; x8 =
**31.5 GB/s**, below the NIC's 400 Gb/s = 50 GB/s line rate, so PCIe becomes the bottleneck.
Achieved at 85 %: 0.85 × 31.5 = **26.8 GB/s**.
DP all-reduce bytes per GPU per step (Section 16.6): 1.75 × 4.375 GB = 7.66 GB.
Time = 7.66 / 26.8 = 0.286 s versus 7.66 / 45 = 0.170 s healthy (90 % of 50 GB/s, as in Section 16.6)
→ **+0.116 s per step = 0.67 %** of 17.4 s, fully exposed `[MODELED]`: with pipeline parallelism only the
last micro-batch's backward pass hides the DP all-reduce (≈ 70 ms window, Chapter 11), and the healthy
0.170 s already exceeds it, so the whole increase lands on the step.
Wrong methods: using 400 Gb/s (the NIC rate) instead of the PCIe ceiling; treating 31.5 GB/s as
bidirectional.

**(c) Which is worse, and why reject both.** The throttling GPU costs 11.0 % versus 0.67 %, about
16× more, because compute sits on the critical path of every step: the whole synchronous job waits
for the slowest GPU. The NIC's DP all-reduce is small relative to the step, even though
none of the increase is hidden. Acceptance must still reject both, because it cannot know which job lands on
the node next: expert-parallel all-to-all, larger DP, inference KV cache transfer, or checkpoint
staging through the same PCIe switch put the NIC on *their* critical path. The lesson of Section
16.6: the cost of a defect depends on the job, so acceptance judges the node against the most
demanding job it may run.

`solve.py` recomputes every value and asserts the key.
