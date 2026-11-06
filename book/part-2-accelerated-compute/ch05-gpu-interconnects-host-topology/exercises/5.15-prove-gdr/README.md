# Exercise 5.15 — Prove GPUDirect RDMA on a real host

★★ · Tier L2 · outline-mandated · kind: `written`

<!-- prompt:start -->
**5.15** ★★ L2 — *Prove GDR.* On a GPU host with an RDMA NIC, collect evidence for each Table 5.3 item,
then run a test that shows GDR in use (or not). *Evidence required:* raw command outputs per item,
NCCL `/GDRDMA` lines or `ib_write_bw --use_cuda` results, and a verdict.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 5 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the Table 5.4 model parameters.
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the model answer and marking scheme in [outputs/expected/](outputs/expected/README.md); compare the reasoning and evidence, not the wording.

## What to submit

Put every deliverable in `outputs/`:

- `outputs/evidence/` — raw command outputs, one file per Table 5.3 item
- `outputs/gdr_test.log` — NCCL log excerpt with the channel lines, or `ib_write_bw --use_cuda` output
- `outputs/answer.md` — the evidence table and your verdict

**Hardware run (course harness).** On the course harness, `python scripts/hw_labs.py run ch05 --device
gpu` (from the repository root) collects every Table 5.3 item the host exposes without root. That means
raw `nvidia-smi topo -m`, PCIe link state, the peer-memory modules, `/proc/cmdline` and the PCI/RDMA
scan. It writes an evidence table and a verdict to `lab/l2/results/<gpu-model>/report.md`, with the raw
outputs in `results.json`. On a host without an RDMA NIC the verdict is "GDR impossible" and item 6 is
recorded as not runnable. Use its raw outputs for `outputs/evidence/` and say so in your verdict. The harness builds and runs a Docker image, so Docker must be running.