# W2 — Sizing a shared pool with Little's law (★★, L1)

Type: worked-problem · Kind: computed

## Prompt

<!-- prompt:start -->
**W2. ★★ L1 — Sizing a shared pool with Little's law.** A document-QA product sends 25 req/s with
4,096-token prompts and 512-token outputs to T-tp4-fp8 replicas (same assumptions as Section 15.12). The
SLOs are TTFT p95 ≤ 800 ms and TPOT p95 ≤ 50 ms; plan for mean TPOT ≤ 35 ms.
(a) Compute prefill time and prefill demand in replica-seconds per second. (b) For 6, 8, 10 and 12
shared replicas, compute ρ_prefill, mean TTFT, mean TPOT and decode batch. Identify any
configuration that is unstable. (c) Pick a pool size and state the worst-case ITL. (d) Check KV
capacity at full sequence length.
*Evidence required:* a table for (b), the fixed-point derivation for one row, and the choice with
justification.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) (W-INFER for serving questions).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Optional: if you script the arithmetic, save the script as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
