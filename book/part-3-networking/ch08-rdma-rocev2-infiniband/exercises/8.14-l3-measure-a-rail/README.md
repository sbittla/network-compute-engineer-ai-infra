# 8.14 — L3 extension: measure a rail (★★★, L3)

Type: Hands-on lab · kind: `written` · 10 points

## Prompt

<!-- prompt:start -->
**8.14 L3 extension: measure a rail** ★★★ · L3
On a dedicated lab fabric, collect real inventories from two nodes, run your validator, then run
`ib_write_bw -a` and `ib_write_lat -a` on at least two rails (five repetitions each, warm-up discarded,
NUMA-pinned). Compare the measured plateau and n½ with the Section 8.11 model for your link speed and
MTU.
*Evidence required:* raw captures; filled-in `manifest.yaml` with `evidence_class: MEASURED`; median
and min/max for plateau and p99/p99.9; model-versus-measured table with an explanation of any gap.
<!-- prompt:end -->

## What to submit

Run only on a dedicated lab fabric. Record the environment in `manifest.yaml` with `evidence_class: MEASURED`. Put every deliverable in `outputs/`:

- `outputs/raw/` (the unedited ib_write_bw / ib_write_lat captures and inventories)
- `outputs/manifest.yaml`
- `outputs/report.md` (median and min/max table, model-versus-measured table, gap explanation)
