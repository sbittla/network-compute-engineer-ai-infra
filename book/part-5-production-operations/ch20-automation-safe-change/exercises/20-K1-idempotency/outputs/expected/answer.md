# 20-K1 — Idempotent operations: worked answer

**Relies on:** manuscript Section 20.3.1 (definition) and Table 20.4 (non-idempotent operations).

## Model answer

An operation is **idempotent** when applying it once or many times leaves the target in the same
end state. The definition is about the *end state*, not about how dangerous the operation is.

- **Naturally idempotent on ORION:** `ip link set dev eth1 mtu 9000` on a backend NIC. The first run
  changes the IP MTU from, say, 1,500 to 9,000 B; every later run finds 9,000 and leaves it at 9,000.
  A gNMI `replace` of a rail leaf's DSCP-to-TC map is idempotent for the same reason: the whole object
  is replaced with the same content.
- **Not idempotent:** a NIC firmware flash followed by a reset (or a reboot, appending a config line,
  allocating an IP address). Every call disrupts the node again, and a re-flash can fail or hit
  anti-rollback rules.

**Making the flash retry-safe.** Gate the action on *observed running state*: read the running
firmware (`ethtool -i <netdev>` → `firmware-version`), flash only if running ≠ target, and read it
back after the reset to confirm. Attach an **idempotency key** per change and target
(for example `CHG-2026-1110/orion-n13`), so that a retry after a timeout returns the earlier result
instead of flashing and resetting a second time. Together these make "run it again" converge to the
same end state, which is what fleet automation needs, because at fleet scale something always times out
and gets retried.

## Marking notes (4 points)

| Criterion | Points |
|---|---|
| Definition in terms of end state | 1 |
| Idempotent ORION example | 1 |
| Non-idempotent ORION example | 1 |
| Retry-safety technique (check running state, read back, idempotency key) | 1 |

**Common wrong answers.** "Idempotent means safe": a reboot can be safe and still not be idempotent.
"Make it idempotent by retrying until it succeeds": retrying a non-idempotent action is exactly the
hazard. Citing `echo "mtu 9000" >> /etc/config` as idempotent: every run appends another line.
