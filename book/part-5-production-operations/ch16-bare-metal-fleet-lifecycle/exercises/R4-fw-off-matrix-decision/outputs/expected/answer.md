# R4 — Waive, reflash, or fast-track a bundle?

**Decision (reference):** do not waive silently. **Reflash** the NIC to the production bundle now so
the node can be enabled, and **fast-track a candidate bundle** that contains the new NIC firmware
through qualification. A time-limited waiver is acceptable only as an explicit, owned exception.

| Option | When it is right | Evidence required | Approval |
|---|---|---|---|
| Reflash to bundle | Default: fast, proven, keeps the fleet on one qualified combination | Read-back of the running version (`mlxfwmanager --query` / Redfish inventory); re-acceptance PASS | Normal change |
| Fast-track candidate bundle | The bug is hurting production and the vendor fix is credible | Vendor release notes for the fix; your own reproduction of the bug on the old firmware *and* of the fix on the new one; pilot nodes from the production image pipeline; full acceptance; canary with a bake (Section 16.8) | Change board; bundle status candidate → production |
| Time-limited waiver | Urgent need, one node, while the bundle is qualified | Documented risk owner, the specific bug to monitor (e.g. link renegotiation counters), expiry date, rollback plan | Named risk owner plus fleet lead |

**Why not just waive.** `FW_OFF_MATRIX` exists because one off-matrix device on an otherwise
compliant node is exactly the RMA-replacement pattern that bundles must catch (lab orion-n23). The
firmware is "not yet qualified": the vendor fix may interact with the RDMA stack or GPU driver
(the three-way couplings of Table 16.5). A waiver without an expiry becomes a permanent
unqualified variant in the fleet.

Source: Section 16.7 (bundle lifecycle: candidate → production → deprecated → retired; at most two
production bundles), Section 16.8.
