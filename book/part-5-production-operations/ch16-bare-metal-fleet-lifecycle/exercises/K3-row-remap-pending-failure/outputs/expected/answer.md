# K3 — Pending row remap versus remapping failure

H100-class HBM has spare rows per bank. When the driver sees an uncorrectable (or repeatedly
correctable) error in a row it schedules that row to be remapped to a spare.

| Condition | What it means | Operational action | RMA? |
|---|---|---|---|
| **Pending remap** (`nvidia-smi -q -d ROW_REMAPPER` → `Pending: Yes`) | A failing row has been recorded and a spare reserved, but the remap takes effect only after a GPU reset; until then the bad row can still be used. | Drain the node (no production work), reset the GPU per the vendor procedure, confirm `Pending: No`, then `dcgmi diag -r 3` before re-acceptance. RMA only if pending remaps recur. | Not by itself |
| **Remapping failure** (`Remapping Failure Occurred: Yes`, Xid 64) | The GPU could not remap: spare rows in that bank are exhausted or the remap operation failed. The memory defect is permanent. | Drain with category `fault`, preserve evidence (`nvidia-bug-report.sh`, DCGM output), open an RMA for the GPU/baseboard. | **Yes** |

**Why the distinction matters.** A pending remap is a normal self-healing step that needs a
maintenance action; a remapping failure means the self-healing mechanism has run out. The lab
plants orion-n30 with `row_remap.pending = true` while `dbe_volatile = 0` (counters reset by a
driver reload): judging only the volatile DBE counter would pass a GPU that must not run
production (`HBM_ROW_REMAP_PENDING`).

**Common wrong answers.** RMA-ing on a single pending remap; returning the node to service after a
reboot without confirming `Pending: No`; treating "volatile DBE = 0" as proof of health.

Source: Section 16.5 ("GPU health: DCGM diagnostics, ECC, and row remapping"), Table 16.4,
runbook Table 16.7a (Xid 63 / Xid 64 rows).
