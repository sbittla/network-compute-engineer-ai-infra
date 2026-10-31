# Exercise 5.15 — Prove GPUDirect RDMA on a real host

★★ · Tier L2 · outline-mandated · kind: `written`

<!-- prompt:start -->
**5.15** ★★ L2 — *Prove GDR.* On a GPU host with an RDMA NIC, collect evidence for each Table 5.3 item,
then run a test that shows GDR in use (or not). *Evidence required:* raw command outputs per item,
NCCL `/GDRDMA` lines or `ib_write_bw --use_cuda` results, and a verdict.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/`:

- `outputs/evidence/` — raw command outputs, one file per Table 5.3 item
- `outputs/gdr_test.log` — NCCL log excerpt with the channel lines, or `ib_write_bw --use_cuda` output
- `outputs/answer.md` — the evidence table and your verdict
