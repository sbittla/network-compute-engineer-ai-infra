# R1 — Intervention evidence still missing: guidance and model answer

**Relies on:** Section 19.5 "Proven cause versus correlation" (intervention as the fourth test); Section
19.11 Steps 5 and 9; lab `data/hypotheses.yaml`, `data/switch_port_counters.csv`, `data/host_nic_snapshot.csv`.

## Statements in the packet that rest on intervention evidence not yet available

1. **"H1 (orionxl-n212 rail-5 link) is the cause."** Timing, locality and mechanism are established from
   `events.jsonl` (link down 9 s before NET/IB status 12; 14 s > 8.6 s budget) and the rank map. But the
   fourth test, *removing the component removes the symptom*, has not run yet. Only the restart without
   n212 can supply it.
2. **"The host optic, not the HCA port, is at fault."** DOM (host TX −5.8 dBm vs fleet ≈ −1.6 dBm,
   switch RX ≈ −6.1 dBm) localizes the transmit path. Optic vs HCA is still a hypothesis until the optic
   is swapped and the link soaks clean.
3. **"orionxl-n389 GPU3 is healthy after reset."** This is a prediction until the pending remap clears and
   `dcgmi diag -r 3` passes.
4. **"Flap-rate quarantine would have prevented attempt 2."** This is a counterfactual. It can only be
   checked by replaying past events against the rule.

## How to obtain the evidence

- **Restart without n212** (spare s01) and require the job to run **≥ 2 × job MTBF (≥ 6 h)** with zero
  rail-5 link events and no hang in stage 3. A recurrence on s01's rail 5 would point at the leaf port
  or fiber instead.
- **Swap the host optic first** (cheapest and matches DOM), then run a **24 h BER soak** on n212 rail 5
  (zero FEC-uncorrectable bursts, RX power back near −2 dBm at the switch) and a rail-5 NCCL test. If
  errors persist, replace the HCA and repeat.
- **Reset n389 GPU3**, verify Pending = No with no remap failure, run diagnostics.
- **Replay the 30-day event history** through the proposed F03 rule to count how many hangs it would
  have prevented and how many healthy nodes it would have drained (false positives).

Until then, the packet should label H1 "proven pending intervention", not just "proven".
