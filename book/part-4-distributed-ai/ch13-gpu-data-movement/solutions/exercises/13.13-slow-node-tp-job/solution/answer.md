# 13.13 — One slow node in a TP job: worked solution

**Symptom.** Step time +12 %. Only the eight ranks on `orion-n09` show **TP communication 3× the
median**. Their compute, clocks and tokens are normal. DP and PP times are normal everywhere. The node
was rebooted for a driver update the previous evening.

**Ranked hypotheses.**

| # | Hypothesis | For | Against |
|---|---|---|---|
| 1 | NVLink degraded on n09: one GPU trained only 6 of its 18 links after the reboot, so its NVLink bandwidth is ≈ 1/3 and every TP collective on the node, gated by that GPU, takes ≈ 3× longer | TP-only, one node, began after a reboot; 18/6 = 3× matches | — |
| 2 | The container on n09 started without IPC/P2P access, so NCCL fell back to the SHM transport through host memory | Also TP-only and node-local; can follow a runtime change made with the driver update | SHM is typically more than 5× slower than NVLink `[ILLUSTRATIVE]`, so 3× fits less well |
| 3 | GPU clocks low | — | **Rejected:** clocks normal, compute normal |
| 4 | Network | — | **Rejected:** DP and PP (the inter-node traffic) normal |
| 5 | Fabric Manager not running after the driver update | Driver-related | **Rejected:** on NVSwitch systems CUDA reports the GPUs as not ready (`cudaErrorSystemNotReady`, "system not yet initialized"), so the job fails at start-up instead of running slowly (Section 13.2) |

**Discriminating tests** `[VENDOR-SPEC, 2026-10]`:

- `nvidia-smi nvlink --status -i <gpu>` for each GPU on n09: healthy shows 18 links at the full rate;
  the bad GPU shows fewer active links.
- `nvidia-smi topo -m`: GPU↔GPU should read `NV18`; the bad GPU's row reads, for example, `NV6`.
- `nvidia-smi nvlink -e` and the DCGM fields `DCGM_FI_DEV_NVLINK_CRC_FLIT_ERROR_COUNT_TOTAL` /
  `…_REPLAY_ERROR_COUNT_TOTAL` / `…_RECOVERY_ERROR_COUNT_TOTAL`: counts rising on the marginal links.
- Single-node `all_reduce_perf -b 8 -e 8G -f 2 -g 8` on n09 against a healthy peer: busbw above
  ≈ 400 GB/s on the peer if NVLS is active (≈ 360–380 GB/s for a plain ring), far lower on n09.
- `NCCL_DEBUG=INFO` on n09: `via P2P/CUMEM` (or `P2P/IPC`) when P2P works; `via SHM` under
  hypothesis 2.

**Most likely root cause (model).** One GPU on n09 came back from the reboot with only 6 of 18 NVLink
links trained (link-training failure, or a marginal connector or NVSwitch port). NCCL kept running, but
every TP collective on the node is gated by that GPU's ≈ 1/3 bandwidth, which gives the 3× TP time. The
whole job slows because TP sits on the critical path and every step waits for the slowest TP group.

**Safe fix.** Checkpoint the job, then drain `orion-n09`. A drain does not move a running job:
restart without the node at reduced DP, or wait for the repair, since ORION-256 has no spare nodes.
Fleet resets the GPU or node, reseats or repairs the faulty link under change control, and runs
acceptance tests before returning the node.

**Validation.** All 18 NVLinks active on every GPU; `topo -m` shows `NV18`; NVLink error counters flat
over a soak; single-node busbw within 5 % of the fleet median; then the node rejoins and the job's TP
time on n09 is within 5 % of the median, with step time back to its pre-incident value `[MEASURED]`
after the fix.
