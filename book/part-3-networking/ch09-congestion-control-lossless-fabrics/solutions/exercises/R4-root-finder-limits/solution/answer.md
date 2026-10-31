# R4 — When the root-finder rule fails (model answer)

Relies on lab README Task 3 (root = congested at ≥ 90 % of line rate and *not* receiving pause), manuscript
Section 9.5 (congestion trees, slow-receiver symptom), Section 9.8 (Figure 9.10, reading counters) and
Section 9.12.

## Situations where "congested and not receiving pause" misidentifies the root

1. **The true root is a slow-receiver host.** In Section 9.12 the bottleneck is a NIC on a PCIe x8 link.
   Its leaf port *receives* pause from the NIC and runs at ≈ 213 Gb/s, below 90 % of line rate. Every
   switch port in the tree is either paused or not at line rate, so the rule finds **no switch root**, or
   names an upstream branch. The root is the *host*. Classify it as storm/slow receiver instead.
2. **Missing samples at the root port.** In a telemetry gap (like the lab's spine-2 gap at 300–310 s)
   the root's rates are NaN, so the rule cannot select it and may promote a branch that does have data.
3. **Two simultaneous roots** (two incasts in one window). The rule returns both, but the tree-walk
   narrative may attribute every branch to one of them.
4. **A counter reset at the root** produces a NaN pause rate. That reads as "not receiving pause"
   only if NaN is mishandled, and it can hide a real pause rx.
5. **Pause rx just under the 100 /s threshold**, or pauses that are brief within a 2 s sample (R2),
   make a branch look like a root.

## Extra evidence to use

- **NIC-side counters:** `pfc_tx_p3` and storm/pause-duration counters on the attached NIC (a host that
  pauses is the root); host `lspci -vv` LnkSta/LnkCap, `dmesg` AER, CPU and memory state.
- **Both-end agreement:** switch `pfc_rx` on one end must match `pfc_tx` on the peer. A disagreement
  flags a counter or telemetry fault.
- **Topology walk of the flows involved:** follow the victims' and senders' paths hop by hop and check
  that the candidate root lies on all of them.
- **Higher-resolution telemetry** (watermarks, pause duration) for the window in question.
