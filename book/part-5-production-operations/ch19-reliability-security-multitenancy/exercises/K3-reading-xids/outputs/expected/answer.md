# K3 — Reading Xids: worked solution

**Relies on:** Section 19.3 "Xid events", Table 19.4 `[VENDOR-SPEC, 2026-10]`.

**Caveat (required for full marks):** Xid meanings and recommended actions are defined by NVIDIA per
GPU generation and driver branch. Table 19.4 is a teaching summary; confirm each code against NVIDIA's
current *Xid Errors* document before acting. Identify the GPU by the PCI address in the
`NVRM: Xid (PCI:…)` line, not by the CUDA index.

| Xid | Hardware or application? | What to do with the node |
|---|---|---|
| 13 — graphics engine exception | Usually **application** (illegal instruction or bad address in a kernel) | Nothing to the node at first. Tell the user, with the job ID and the log line. Investigate hardware only if Xid 13 recurs on the *same GPU* across *different* jobs and users |
| 79 — GPU has fallen off the bus | **Hardware** (PCIe link, power, thermal, board) | Drain the node; capture `nvidia-bug-report.sh`, `dmesg`, AER counters before rebooting; cold reboot (power cycle, not just a warm reboot); run DCGM diagnostics; RMA if it repeats |
| 94 — contained ECC error | **Hardware**, but contained: the affected contexts were killed and the GPU can continue | Restart the affected job (it can run elsewhere or here); drain the node when convenient, reset the GPU, check the row remapper (Pending/Failure, see K2) before return |

## Reading the sequence

Three different codes in a week on one node are three separate events with different owners. Xid 13
says nothing about the hardware by itself. Xid 79 is the serious one: the node should already be drained
and in diagnostics when the Xid 94 arrives. A week of escalating hardware codes (79, then 94) on one GPU
is a strong case for replacement even if each event alone passed diagnostics.

Contrast with Xid 95 (uncontained ECC): all contexts on the GPU are affected, so drain immediately rather
than "when convenient".

## Common wrong answers

- Calling Xid 13 a hardware fault and draining the node on the first occurrence.
- Treating Xid 79 as recoverable by a GPU reset alone: the device is off the bus, so a cold reboot and
  diagnostics are needed.
- Confusing Xid 94 (contained) with Xid 95 (uncontained), or with Xid 48 (double-bit ECC).
- Omitting the vendor-document caveat.
