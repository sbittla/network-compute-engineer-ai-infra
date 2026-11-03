# 6.3 — 4.6 TB/s of "DRAM" bandwidth on a 3.35 TB/s GPU (model answer, 3 points)

Relies on manuscript Section 6.3 ("What the roofline does not tell you") and Lab 6 trap T7.

First principle: the value exceeds the 3.35 TB/s HBM roof, so it **cannot be DRAM bandwidth**. Something in the
measurement is wrong or the bytes did not come from DRAM.

**Mechanism 1 (1 point): part of the traffic never left the chip.** The input may still be in L2 from the
producer kernel, or the output may still sit in L2 write-back when the timer stops, so those accesses never
reach HBM and bytes ÷ time partly measures L2 throughput. This explains only what fits: the L2 is 50 MB,
two ≈ 25 MB partitions on this GPU class `[VENDOR-SPEC, 2026-10]`. Lab 6's `bias_add_l2_resident`
(100.7 MB in 20 µs = 5.03 TB/s `[SIMULATED]`) cannot be fully L2-resident, so its shape-derived byte count
also overstates DRAM traffic (mechanism 2).

**Mechanism 2 (1 point): the bytes are computed, not counted.** "Bandwidth" was derived from tensor shapes
(inputs + outputs × element size), which double-counts operands read once but listed twice, assumes a layout
or precision the kernel did not use, or ignores fusion that removed a write.

**What to check (1 point).** In Nsight Compute, read the DRAM counters `dram__bytes_read.sum` and
`dram__bytes_write.sum` and compare with the L2 counter `lts__t_bytes`; if DRAM bytes ≪ computed bytes, the
data came from L2. Or rerun with an input several times larger than L2 (e.g. ≥ 500 MB): the apparent bandwidth
should fall below the roof. Then compare computed bytes with measured DRAM bytes to find the accounting error.

**Common wrong answers.** "The GPU is faster than spec" or "HBM overclocking"; reporting it as the fastest
kernel.
