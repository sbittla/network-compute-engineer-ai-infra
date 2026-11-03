# K9 — Silent data corruption: worked solution

**Relies on:** Section 19.4 ("Silent data corruption", and its row in Table 19.5); Section 19.7
(checkpoint selection).

**Why nothing fired.** Every detector in Tables 19.4–19.5 reacts to an *error* or a *stall*: Xids and
row-remap events come from ECC and driver checks, AER from the PCIe link layer, NET/IB warnings from
transport retries, and the watchdog from a collective that never completes. A component that computes
wrong values raises none of these. ECC protects stored bits, not arithmetic, and the all-reduce completes
normally, averaging the bad gradient into every replica. The only symptom is in the numbers: the loss
spike.

**Finding the node (any two, with the mechanism):**
- Date the onset from the loss and gradient-norm history (z-score against a rolling window). A spike that
  follows one step points to a gradient error that the all-reduce spread to every replica.
- Compare a checksum of one parameter shard across DP replicas. A replica that drifts has a fault in its
  local update path (optimizer step, weights), not in its gradient.
- Golden-batch replay: re-run step 41,200 with the same inputs, seed, and weights on suspect nodes and on
  a known-good node, and compare outputs bit for bit (or within a stated tolerance). Bisect across
  DP-replica subsets to reach one node.
- Deep diagnostics on the suspects: `dcgmi diag -r 3` or `-r 4`, plus vendor SDC screens
  `[VENDOR-SPEC, 2026-10]`.

**Restore choice.** Restore the newest checkpoint written *before* the onset (before step 41,200), not the
newest checkpoint. Checkpoints written after the onset may already hold corrupted weights. Quarantine the
node with its replay evidence for the vendor before restarting.

**Common mistake:** restarting from the latest checkpoint, or assuming that because health checks pass the
hardware is fine.
