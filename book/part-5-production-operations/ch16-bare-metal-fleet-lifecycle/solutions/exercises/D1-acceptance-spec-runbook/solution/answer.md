# D1 — Node acceptance specification and lifecycle runbook (reference outline)

A full-mark document assembles the earlier exercises into one operational specification:

1. **Acceptance specification (from M1).** The policy file (the lab's `acceptance_policy.yaml`
   extended to ≥ 12 checks in fail-fast order), with a rationale per check: what defect it catches,
   why it runs where it does in the order, and how its threshold was set (median − margin from a
   known-good population, R1). Every threshold carries an evidence label; FAIL vs WARN is explicit
   (WARN: SBE > 10, deprecated bundle). Duration ≈ 25.4 h per node, `policy_version` recorded.
2. **Evaluator input schema and reason-code catalogue (from the lab).** The JSON fields of
   `acceptance_results.json` per check, and every code with its meaning and remediation:
   `GPU_COUNT`, `GPU_PRODUCT`, `HBM_CAPACITY`, `PCIE_DEGRADED`, `NVLINK_DOWN`, `ECC_DBE`,
   `HBM_ROW_REMAP_PENDING`, `HBM_ROW_REMAP_FAILURE`, `ECC_SBE_ELEVATED` (WARN), `DCGM_DIAG_FAIL`,
   `THERMAL_THROTTLE`, `NIC_LINK_DOWN`, `NIC_SPEED`, `NIC_COUNT`, `NIC_MTU`, `RDMA_PAIR_BW_LOW`,
   `NVME_COUNT`, `NVME_MEDIA_ERRORS`, `STORAGE_THROUGHPUT_LOW`, `NCCL_BUSBW_LOW`,
   `NCCL_ALGO_UNRECORDED`, `XID_PRESENT`, `FW_OFF_MATRIX`, `FW_DEPRECATED` (WARN).
3. **State machine (from M3)** with the 13-transition table, guards, forbidden transitions and
   reasons, and the audit-record schema (`seq, ts, node, event, actor, from_state, to_state, result,
   reason_code`, plus ticket/change/waiver/certificate IDs).
4. **Compatibility matrix process and staged upgrade (from M2):** bundle lifecycle, per-device
   firmware checks, at most two production bundles; the canary/wave plan with derived numbers
   (76 % canary detection, 8 waves, 195 h, 768 GPU-hours), abort gates, rollback per component.
5. **Runbook** for "node fails acceptance" and "node develops a hardware fault in production",
   built on Table 16.7a: signals (Xid classes, remap pending, PCIe width, thermal slowdown, NIC speed,
   RDMA pair bandwidth, off-matrix firmware, rising SBE), thresholds, safe actions (drain category
   `fault` via the lifecycle service, preserve evidence *before* reboot, smallest replaceable unit,
   re-acceptance), evidence to capture (`nvidia-bug-report.sh`, DCGM, `dmesg`, SEL, switch-port
   counters), and escalation (Fleet, Fabric, Facilities, vendor RMA). Must state the rule "never
   resume a fault-drained node without re-acceptance".
6. **Realism section:** what was validated at L1 only (logic of acceptance, guards, planning) and what
   needs L2/L3 evidence (burn-in physics, real failure signatures over time, BMC activation
   behaviour, end-to-end path MTU), and that thresholds and version strings are teaching values.

**Appendix:** the lab `acceptance_report.md` (25 PASS / 1 WARN / 6 FAIL with raw values and
remediation) and the checker output (33/33).

**Grading notes.** Deduct under criterion 4 if numbers are asserted rather than derived, and under
criterion 5 if any runbook path skips evidence preservation or re-acceptance.

## Hardware run

`python scripts/hw_labs.py run ch16 --device gpu` produces the L2 appendix for section (6), the realism section.
It collects the GPU part of an acceptance record from a real device: inventory, PCIe link idle and under load,
row-remapper state, a memory write/verify test, a GEMM check and a short burn-in with clock-event-reason telemetry.
It then runs the lab's `evaluate_node` on that record with policy `acc-2026.10`, with only `expected` adapted to the
SKU. The bundle in `lab/l2/results/` (`environment.json`, `results.json`, `report.md`) is the "raw command output"
the prompt asks for, and its not-runnable table names each check that stays L1-only on a one-GPU host: NVLink, ECC,
DCGM, RDMA NICs, NVMe/fio, multi-GPU NCCL, Xid and BMC firmware. Without a GPU (`--device cpu`) the run falls back
to a host-RAM pattern test and a CPU burn-in, and the evaluator must fail the GPU-less host with `GPU_COUNT`.
