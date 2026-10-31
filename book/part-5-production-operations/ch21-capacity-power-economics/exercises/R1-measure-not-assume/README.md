# R1 — Measured rather than assumed (★, L1)

Type: Reflection · Kind: `written` · Points: 6

## Prompt

<!-- prompt:start -->
**R1 ★ L1** — Which three inputs in your lab model would you most want measured rather than assumed, and
how would you measure each?
<!-- prompt:end -->

Shared evidence line for R1–R4 (from `exercises.md`): *Evidence required (R1–R4):* concise answers citing sections or data files.

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/answer.md`

On a single GPU host, `python scripts/hw_labs.py run ch21 --device gpu` measures power vs throughput at the default limit
(CPU fallback with `--device cpu`). The cap sweep itself is reported as not runnable without root on bare metal.
