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

## What to submit

Draw both data paths (Mermaid or hand-drawn, saved as an image or Markdown) and give a count table per side. Put every deliverable in `outputs/`:

- `outputs/answer.md`
- `outputs/diagrams.md` (Mermaid source) or diagrams.png
