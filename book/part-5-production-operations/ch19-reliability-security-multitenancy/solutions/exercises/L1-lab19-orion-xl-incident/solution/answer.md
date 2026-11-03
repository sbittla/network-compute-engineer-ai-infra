# L1 — Lab 19: ORION-XL incident: reference solution

**Relies on:** lab/README.md Sections 6 and 8; manuscript Sections 19.3–19.11; reference implementation
`solutions/lab/incident_toolkit.py`; data in `lab/data/` `[SIMULATED]`. Arithmetic `[MODELED]`.

## Checker

`python check.py --impl solution` reports **12/12 checks passed**. The lab checks recorded in
`outputs/lab_checks.json` are the twelve PASS lines, from `dataset reproducible` through
`T6 tenant isolation checker`.

## Reference results (what each task must produce)

| Task | Reference result |
|---|---|
| T1 parsers / rank map | Xid line → `{pci: 0000:5d:00, xid: 63}`; NET/IB → peer 10.135.1.167, status 12, `mlx5_5`; rank 1693 → orionxl-n212, GPU5 `0000:ab:00.0`, NUMA 1, `mlx5_5`, orionxl-be-leaf-p06-r5 Ethernet20/1; Xid PCI on orionxl-n389 → rank 3107 |
| T2 stuck group | 64 ranks at `last_completed_seq` 88212 (others 88213): local rank 5 on orionxl-n193–n256, rail 5, PP stage 3, leaves p06-r5 and p07-r5 |
| T2 link implication | Endpoint scores orionxl-n212 = 3, n211 = 2, n213 = 1; bad port p06-r5 Ethernet20/1: 4 link-downs, FEC-uncorrectable +203,903, RX −5.6 to −6.4 dBm; host TX −5.8 dBm |
| T2 GPU health | n389 GPU3 `drain_reset_validate`; n046 GPU6 `monitor`; s00 GPU2 `quarantine_rma` |
| T3 hypotheses | H1 proven_cause; H2 real_fault_not_cause; H3, H4, H5 correlation_only; H6 refuted |
| T4 checkpoint and metrics | `ckpt-0084` (ckpt-0085 metadata uncommitted). Attempt 2: RPO 31.03 min, RTO 49.97 min, 5,529.6 GPU-h. Attempt 1: RPO 12.73 min, RTO 39.43 min, 3,561.2 GPU-h |
| T4 retry policy | orionxl-n212 repeat offender → auto-restart blocked until it is excluded |
| T4 restart plan | n212 → orionxl-s01 (ranks 1688–1695); n389 → orionxl-s03 (ranks 3104–3111); local ranks preserved |
| T5 FMEA | Top F03 (RPN 336); F07 DETECTION_INCONSISTENT (re-scored 200); F11 OUT_OF_RANGE; action set F03, F06, F07, F12 |
| T6 isolation | 11 violations |

## Incident packet: the items the rubric marks

1. **Failure timeline (15).** 23:10:05 attempt 1 starts. 01:12:44 n212 `mlx5_5` link down (14 s).
   01:12:53 NET/IB status 12 from n211/n212/n213. 01:23:40 900198 FAILED; auto-requeue on the *same*
   allocation. 01:40:02 attempt 2 starts; 01:52:10 resumes from ckpt-0081. 02:47:03 6 s flap and 03:29:50
   5 s flap, both survived. 02:58:41 n389 GPU3 Xid 63, remap pending. 03:40:00 ckpt-0085 starts; shards
   done at 03:40:58 but metadata in progress. 03:41:02 14 s flap. 03:41:11 NET/IB errors. 03:41:20 spine
   PFC spike. 03:51:01 first watchdog (rank 817). 03:52:15 FAILED, requeue held. 04:31:00 resume on
   spares from ckpt-0084.
2. **Rank-to-hardware table (10)** for ranks 1685, 1693, 1701 (rail 5, n211–n213), the 64 stuck ranks
   summarized, and 3107 (n389 GPU3, `0000:5d:00.0`, NUMA 0, `mlx5_3`, p12-r3): columns rank, node, GPU
   UUID, BDF, NUMA, HCA, rail, leaf port.
3. **Proven vs correlated (20).** H1 cites *timing* (link-down 9 s before the first NET/IB error; 14 s >
   8.6 s budget), *locality* (rail 5, stage 3, the stuck group's path; top endpoint), and *mechanism*
   (retry exhaustion → status 12 → hang). It is proven **pending intervention**: the restart without
   n212 must run clean. H2 is real but 42 min earlier, and its ranks completed 88213. H3: watchdog order
   is arbitrary. H4: corrected AER every ≈ 40 min all night, on a node that is not stuck. H5 starts
   *after* the fault, so it is a consequence. H6: 1 of 32 ports bad, so refuted.
4. **Health decision (15).** n212: the fault domain is the host transmit path (host optic first, then
   HCA port); the unit removed is node n212. n389: GPU3 pending remap; unit n389 for this restart; reset
   and validate. n046: monitor. Leaf p06-r5: not quarantined. s00: ineligible, RMA.
5. **Restart plan (15).** Restore ckpt-0084 and validate shard count, checksums and metadata. Map
   spares s01 and s03 with local ranks preserved. Pre-restart: DCGM and link checks on spares, n212 and
   n389 excluded. Post-restart: first-step loss consistent with step 151799, step time within 5 % for
   30 min, zero link events. Retry policy: ≤ 2 automatic restarts per 6 h, implicated nodes excluded
   first.
6. **Metrics (5).** As in the table. The first auto-restart onto the same nodes cost attempt 2's
   5,529.6 GPU-h. Total ≈ 9,091 GPU-h ≈ $27,300 at $3.00/GPU-h.
7. **Risk register (10)** top 5: F03 336, F07 200 (corrected), F12 189, F08 140, F06 (severity override).
   Each needs an owner and a mitigation.
8. **Isolation (10):** all 11 violations with remediation (see M2).

## Deductions to apply

Quarantining orionxl-be-leaf-p06-r5 or all of rail 5 (blast-radius error); restoring ckpt-0085; choosing
orionxl-s00; calling H1 proven with no intervention test.
