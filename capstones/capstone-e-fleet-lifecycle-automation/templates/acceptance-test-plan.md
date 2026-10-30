# Node Acceptance Test Plan — HX8

> Template for Capstone E artifact 2. Every threshold needs a source and an evidence label:
> `[VENDOR-SPEC, YYYY-MM]`, `[MEASURED]` (calibration on named golden nodes), `[MODELED]` (show the
> formula) or `[ILLUSTRATIVE]` (L1 only). Replace every `<fill: …>`.

**Policy version:** `<fill: acceptance-YYYY.MM>` · **Applies to:** `<fill: platform / bundle>` ·
**Calibration nodes:** `<fill: node names + dates, or "L1: none — ILLUSTRATIVE">`

## 1. Entry and exit criteria

- Entry: node in `imaged`; image ID recorded; `<fill>`
- Exit (pass): every gating test passes, evidence `started_utc` > `image_completed_utc`, results
  stored under `<fill: evidence store path / object key>` with SHA-256 recorded in the audit log
- Exit (fail): node → `repair` with failing test names; `<fill: ticket auto-created? owner?>`

## 2. Test matrix

| # | Area | Test (tool, command, tier) | Metric | Threshold | Source / arithmetic | Gating? | Duration |
|---|---|---|---|---|---|---|---|
| 1 | Accelerator discovery | `nvidia-smi --query-gpu=index,uuid,pci.bus_id --format=csv` (L2) | GPU count | = 8 | platform spec | yes | < 1 min |
| 2 | PCIe | `<fill>` | gen / width per GPU and NIC | ≥ Gen5 x16 | `<fill>` | yes | `<fill>` |
| 3 | NIC link | `<fill>` | speed per rail | = 400 Gb/s | `<fill>` | yes | `<fill>` |
| 4 | GPU memory health | `<fill: ECC + row-remap query>` | uncorrectable ECC; pending/failed remaps | 0 | `<fill>` | yes | `<fill>` |
| 5 | Correctable ECC | `<fill>` | count | `<fill: trend only? alert at?>` | `<fill>` | `<fill: justify>` | `<fill>` |
| 6 | Diagnostics | `dcgmi diag -r 3` (L2) | result | pass | `<fill>` | yes | `<fill>` |
| 7 | NVLink | `<fill>` | min device-to-device GB/s | `<fill>` | `<fill: fraction of 450 GB/s per direction>` | yes | `<fill>` |
| 8 | Host↔device | `<fill>` | min H2D GB/s | `<fill>` | `<fill: fraction of ≈63 GB/s>` | yes | `<fill>` |
| 9 | RDMA | `<fill: ib_write_bw per rail, L3>` | min Gb/s | `<fill>` | `<fill: fraction of 400 Gb/s>` | yes | `<fill>` |
| 10 | Collectives | `<fill: all_reduce_perf intra-node>` | bus bandwidth | `<fill: state whether NVLS is assumed; ring-only ceiling ≈ 257 GB/s algbw>` | `<fill>` | `<fill>` | `<fill>` |
| 11 | Storage | `<fill: fio>` | read GB/s | `<fill>` | `<fill: path check vs fleet claim>` | yes | `<fill>` |
| 12 | Thermals | `<fill>` | max GPU temp during burn-in | `<fill>` | `<fill>` | yes | — |
| 13 | Burn-in | `<fill: workload>` | hours, Xid count | `<fill>` | `<fill: infant-mortality rationale and GPU-hour cost>` | yes | `<fill>` |
| 14 | Evidence freshness | timestamps | started > image_completed | — | policy | yes | — |
| 15 | `<fill>` | `<fill>` | `<fill>` | `<fill>` | `<fill>` | `<fill>` | `<fill>` |

## 3. Worked threshold derivations

Show formula → values → result for each bandwidth threshold. Example form:

> RDMA write threshold = line rate × efficiency floor = `<fill>` Gb/s × `<fill>` = `<fill>` Gb/s `[label]`

## 4. Failure handling

| Failing test | First suspect | Next diagnostic | Typical fix | Re-test scope |
|---|---|---|---|---|
| gpu_count | `<fill>` | `<fill>` | `<fill>` | full |
| nic_link_speed | `<fill: optic / cable / port config>` | `<fill>` | `<fill>` | `<fill>` |
| `<fill>` | `<fill>` | `<fill>` | `<fill>` | `<fill>` |

## 5. Cost of acceptance

`<fill: GPU-hours per node and for this week's batch, with arithmetic; argument for/against shortening burn-in>`

## 6. What this plan does not catch

`<fill: at least three failure classes (e.g. intermittent link flaps after admission, cross-node fabric congestion, slow HBM degradation) and which runtime signal covers each>`
