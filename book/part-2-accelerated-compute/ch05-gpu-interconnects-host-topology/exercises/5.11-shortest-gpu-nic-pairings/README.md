# Exercise 5.11 — Shortest GPU-NIC pairings

★ · Tier L1 · outline-mandated · kind: `computed`

<!-- prompt:start -->
**5.11** ★ L1 — *Shortest GPU–NIC pairings.* Using Figure R.1 (REFERENCE_CLUSTER.md) and the `orion-n01`
`nvidia-smi topo -m` capture, list for each GPU the NIC with the shortest data path and its label, and
name one GPU–NIC pair of each class PXB, PHB, NODE and SYS. *Evidence required:* 8-row table plus four
examples, quoting matrix cells.
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 5 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the Table 5.4 model parameters.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — the working: formula → substitution → result, with units and an evidence label on every number

If you script the parsing (recommended), save it as `outputs/solve.py` and run it from this folder against `../../lab/data/hosts/orion-n01/nvidia-smi_topo_m.txt`:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```
