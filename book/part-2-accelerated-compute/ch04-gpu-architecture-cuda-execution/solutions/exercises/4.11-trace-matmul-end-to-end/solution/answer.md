# 4.11 — Trace a BF16 GEMM end to end (model answer)

Relies on manuscript Section 4.3 ("Tracing the vector add end to end"), Section 4.5 (asynchrony) and
Section 4.6 (pinned memory, synchronization). Stage times `[MODELED]`; `solve.py` asserts them.

## (a) Sequence and waits

```text
CPU  : launch H2D(A) ─ launch H2D(B) ─ launch GEMM ─ launch D2H(C) ─ cudaStreamSynchronize ███████ (CPU WAITS) ─▶ uses C
       (each call returns in µs: pinned + async)
PCIe :  [ H2D A 2.58 ms ][ H2D B 2.58 ms ]                     [ D2H C 2.58 ms ]
SMs  :  ······ idle: waits for A and B ·······[ GEMM 1.59 ms ]· idle ·
                                              ▲ GPU waits on H2D     ▲ D2H waits on GEMM (same stream)
```

The CPU waits only at the final synchronize. The SMs wait for both H2D copies (stream order), and the D2H
copy waits for the kernel. With pinned memory the copy calls are asynchronous; with pageable memory each copy
call would also block the CPU.

## (b) Stage times

Each matrix: 8,192² × 2 B = **134,217,728 B** (128 MiB).

| Stage | Formula → substitution | Time |
|---|---|---|
| H2D (A, B) | 2 × 134,217,728 B / 52 × 10⁹ B/s | **5.16 ms** |
| GEMM | 2*N*³ = 2 × 8,192³ = 1.0995 × 10¹² FLOP / (0.70 × 989 × 10¹² FLOP/s = 6.923 × 10¹⁴) | **1.59 ms** |
| D2H (C) | 134,217,728 B / 52 × 10⁹ B/s | **2.58 ms** |
| Total | 5.16 + 1.59 + 2.58 | **≈ 9.33 ms** (kernel 17 %) |

## (c) How real training avoids it

Weights, gradients, optimizer state and activations stay **resident in HBM** across steps; nothing large
crosses PCIe per GEMM. Only the input batch (small: token IDs) is copied, from a reused pinned buffer on a
side stream one step ahead, so the copy overlaps compute. Results stay on the GPU; only scalars (loss) are
read back, and rarely, to avoid synchronizations. Why it must be so: moving the operands per use gives an
intensity of 1.0995 × 10¹² / (3 × 134.2 × 10⁶ B) ≈ **2,730 FLOP/B**, while the "PCIe ridge" is
989 × 10¹² / 52 × 10⁹ ≈ **19,000 FLOP/B**: the GEMM would be PCIe-bound by ≈ 7×.

**Common wrong answers.** Using 4 B per element (FP32); counting one H2D instead of two; showing the CPU
waiting after each copy; overlapping the D2H with the GEMM on the same stream.
