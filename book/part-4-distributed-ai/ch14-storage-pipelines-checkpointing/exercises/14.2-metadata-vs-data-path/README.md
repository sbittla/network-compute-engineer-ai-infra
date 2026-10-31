# 14.2 — Metadata path versus data path (★, L1)

Type: knowledge-check · Kind: written

## Prompt

<!-- prompt:start -->
**14.2 Metadata path versus data path** ★ · L1
In a Lustre-class parallel file system, which server handles `open()`, which handles `read()`, and
what does a client obtain at open time that lets it bypass the metadata server afterwards? Explain
what stripe count and stripe size control, and give one case where *wider* striping does not help.
*Evidence required:* a labelled sketch or numbered sequence of the RPCs for open → read → close.
<!-- prompt:end -->

## What to submit

Put every deliverable in `outputs/` in this folder:

- `outputs/answer.md`

Label every number `[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`.
