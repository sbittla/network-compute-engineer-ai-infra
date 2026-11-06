# 8.10 — Draw the TCP and RDMA data paths (★, L1)

Type: Outline-mandated · kind: `written` · 10 points

## Prompt

<!-- prompt:start -->
**8.10 Draw the two data paths** ★ · L1 *(course outline, Chapter 8 exercise 1)*
Draw the data path for a 1 MiB message sent with TCP sockets and with an RDMA WRITE between two
ORION nodes. For each side, count CPU copies, DMA transfers, system calls, interrupts, and context
switches, and mark where the kernel and the remote CPU are involved. State which offloads would change
your counts and which counts they cannot remove.
*Evidence required:* two labelled diagrams (Mermaid or hand-drawn); a count table per side; offload
discussion.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check your answer against the evidence the prompt asks for. After you have written it, compare it with the worked answer and marking scheme in the chapter's `solutions/exercises/8.10-two-data-paths/` (instructor material in the full repository; removed from student releases).

## What to submit

Draw both data paths (Mermaid or hand-drawn, saved as an image or Markdown) and give a count table per side. Put every deliverable in `outputs/`:

- `outputs/answer.md`
- `outputs/diagrams.md` (Mermaid source) or diagrams.png
