# Exercise 5.12 — P2P versus host-staged transfer

★★ · Tier L1 · outline-mandated · kind: `computed`

<!-- prompt:start -->
**5.12** ★★ L1 — *P2P versus host-staged.* For a 4 GiB transfer GPU2 → GPU6 on HX8: (a) list the copies,
memory locations and synchronization points for NVLink P2P and for a host-staged transfer with pinned
buffers; (b) repeat for pageable buffers; (c) estimate times with 370 GB/s NVLink and 52 GB/s PCIe per
direction, unpipelined and pipelined in 64 MiB chunks; (d) which socket's memory should host the staging
buffer, and why is that awkward here? *Evidence required:* annotated lists, four times, NUMA argument.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the Table 5.4 model parameters.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare your method with the worked solution and marking scheme in the chapter's `solutions/exercises/5.12-p2p-vs-host-staged/` (instructor material in the full repository; removed from student releases).

## What to submit

Put every deliverable in `outputs/`:

- `outputs/answer.md` — the working: formula → substitution → result, with units and an evidence label on every number

If you script the arithmetic (recommended), save it as `outputs/solve.py` and run it from this folder:

```bash
python outputs/solve.py --out outputs/   # optional: your own script; --out is the folder it writes to
```
