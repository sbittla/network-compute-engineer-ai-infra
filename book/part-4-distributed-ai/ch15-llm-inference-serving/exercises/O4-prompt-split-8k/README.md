# O4 — Prompt workload split across prefill and decode pools (★★★, L1)

Type: outline-mandated · Kind: computed

## Prompt

<!-- prompt:start -->
**O4. ★★★ L1 — Prompt workload split across prefill and decode pools (Section 15.10).** Change the
disaggregation workload to **10 req/s with 8,192-token prompts** (256-token outputs). Estimate the
KV bytes per request, the aggregate transfer bandwidth at that rate, and the per-request transfer
time over RDMA and TCP (lab assumptions). Compare a shared-pool design with disaggregated serving
over RDMA and TCP. Then discuss per-layer streaming overlap: can TCP hide the transfer if its
link is uncontended? Repeat the bandwidth estimate with FP8 KV.
*Evidence required:* KV bytes, Gb/s, transfer times, a three-row comparison, the overlap
calculation per layer, and a statement of which values are modeled and which would need L3
measurement.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 15 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
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
