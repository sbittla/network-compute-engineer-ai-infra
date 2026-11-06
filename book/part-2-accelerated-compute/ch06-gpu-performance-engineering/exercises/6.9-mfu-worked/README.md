# Exercise 6.9 — MFU of a 13B-parameter training job

★★ · Tier L1 · worked problem · kind: `computed`

<!-- prompt:start -->
**6.9** ★★ L1 — *MFU.* A 13 × 10⁹-parameter dense model trains on 64 ORION GPUs with 512 sequences ×
4,096 tokens per step at 5.2 s per step; nvidia-smi shows 98 % utilization. (a) MFU; (b) HFU with full
activation recomputation; (c) the MFU someone would report using the FP8 peak by mistake; (d) what the
98 % tells you. *Evidence required:* three numbers with arithmetic and one explanation.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the Table 6.1 ceilings (989 TFLOP/s dense BF16, 1,979 TFLOP/s FP8, 67 TFLOP/s FP32 SIMT, 3.35 TB/s HBM).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare your method with the worked solution and marking scheme in the chapter's `solutions/exercises/6.9-mfu-worked/` (instructor material in the full repository; removed from student releases).

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — the working: formula → substitution → result, with units and an evidence label on every number

If you script the arithmetic (recommended), save it as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```
