# O4 — Prompt workload split across prefill and decode pools (★★★, L1)

Type: outline-mandated · Kind: computed

## Prompt

<!-- prompt:start -->
**O4. ★★★ L1 — Prompt workload split across prefill and decode pools (Section 20.2).** Change the
disaggregation workload to **10 req/s with 8,192-token prompts** (256-token outputs). Estimate the
KV bytes per request, the aggregate transfer bandwidth at that rate, and the per-request transfer
time over RDMA and TCP (lab assumptions). Compare a shared-pool design with disaggregated serving
over RDMA and TCP. Then discuss per-layer streaming overlap: can TCP hide the transfer if its
link is uncontended? Repeat the bandwidth estimate with FP8 KV.
*Evidence required:* KV bytes, Gb/s, transfer times, a three-row comparison, the overlap
calculation per layer, and a statement of which values are modeled and which would need L3
measurement.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Run:

```bash
python solution/solve.py --out outputs
```

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
