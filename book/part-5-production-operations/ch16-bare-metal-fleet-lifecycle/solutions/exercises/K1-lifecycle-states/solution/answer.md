# K1 — Lifecycle states and the only roads to schedulable

**States in order (Figure 16.1, Section 16.1):**
`discovered → imaged → validated → schedulable → draining → drained → repair → retired`.

**Sources of `schedulable`.** Exactly two edges enter `schedulable`:

| From | Event | Guard |
|---|---|---|
| `validated` | `enable` | firmware bundle check passes (node matches a production bundle) |
| `draining` | `cancel_drain` | drain category is `maintenance` (a fault drain cannot be cancelled) |

**Why there is no `repair → schedulable` edge.** A node leaves `repair` with changed hardware or
firmware (a swapped NIC arrives with factory firmware, a reseated GPU may still be marginal), so
nothing about it has been proven; it must re-enter at `imaged` (event `reimage`, guard: ticket
closed) and pass acceptance to reach `validated` before it can be enabled. "The tech swapped the
NIC, just resume it" is exactly how a wrong-firmware NIC lands in a 256-GPU job.

**Common wrong answers.**
- Listing `imaged → schedulable` as a source: that edge is forbidden for the same reason (no
  acceptance verdict yet). The lab's `T3.invariant_no_shortcut_to_schedulable` check enforces it.
- Forgetting the maintenance-only `cancel_drain` path, or allowing it for fault drains.
- Treating `retired` as re-enterable; it is terminal and needs a sanitization certificate.

Source: Section 16.1 ("The lifecycle state machine") and Figure 16.1; lab Task 3.
