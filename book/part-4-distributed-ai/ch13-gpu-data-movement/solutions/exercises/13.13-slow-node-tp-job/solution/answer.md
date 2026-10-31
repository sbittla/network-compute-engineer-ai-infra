# 13.13 — One slow node in a TP job: worked solution

**Symptom.** Step time +12 %. Only the eight ranks on `orion-n09` show **TP communication 3× the
median**. Their compute, clocks and tokens are normal. DP and PP times are normal everywhere. The node
was rebooted for a driver update the previous evening.

**Ranked hypotheses.**

| # | Hypothesis | For | Against |
|---|---|---|---|
| 1 | NVLink/NVSwitch path degraded on n09: fabric-management service not running or links down, so P2P falls back to PCIe/host | TP-only, one node, began after a driver update | — |
| 2 | NCCL topology misdetected (container/driver mismatch) and chose a non-NVLink transport | Also driver-related, also TP-only | Would usually affect every node using the same image |
| 3 | GPU clocks low | — | **Rejected:** clocks normal, compute normal |
| 4 | Network | — | **Rejected:** DP and PP (the inter-node traffic) normal |

**Discriminating tests** `[VENDOR-SPEC, 2026-10]`:

- `nvidia-smi nvlink --status` on n09: healthy shows all links active at full rate. Degraded shows
  inactive links or fewer of them.
- `nvidia-smi topo -m`: GPU↔GPU should read `NV18`. A PCIe label (`PIX`/`PHB`/`SYS`) means no NVLink
  path.
- `systemctl status nvidia-fabricmanager` (or the platform's fabric-management service): expect
  `active (running)`. Look for a version-mismatch error in its journal.
- Single-node `all_reduce_perf -b 8 -e 8G -f 2 -g 8` on n09 against a healthy peer: busbw ≈ 450 GB/s
  (with NVLS) on the peer versus far lower on n09.
- `NCCL_DEBUG=INFO` on n09 shows `P2P/IPC` over NVLink when healthy, or SHM/PCIe transports when not.

**Most likely root cause (model).** The fabric-management service failed to start after the driver
update because its version no longer matched the driver. NVSwitch was not configured, and intra-node
P2P fell back to a PCIe/host path. That fits a 3× TP slowdown on one node, with the whole job slowing
because TP sits on the critical path and every step waits for the slowest TP group.

**Safe fix.** Checkpoint the job, then drain `orion-n09`. A drain does not move a running job:
restart without the node at reduced DP, or wait for the repair, since ORION-256 has no spare nodes.
Fleet aligns the fabric-manager and driver versions under change control, reboots, and runs
acceptance tests before returning the node.

**Validation.** All NVLinks active; `topo -m` shows `NV18`; single-node busbw within 5 % of the fleet
median; then the node rejoins and the job's TP time on n09 is within 5 % of the median, with step time
back to its pre-incident value `[MEASURED]` after the fix.
