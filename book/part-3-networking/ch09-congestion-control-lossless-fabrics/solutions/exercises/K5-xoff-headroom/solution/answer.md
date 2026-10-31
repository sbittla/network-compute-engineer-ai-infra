# K5 — Xoff threshold versus headroom (worked solution)

Relies on manuscript Section 9.4 ("Xoff, Xon, and why headroom exists", "The headroom formula",
Table 9.2, and the pitfall box).

## Definitions

- **Xoff** is a *threshold*: the ingress priority-group (PG) occupancy for a lossless priority at which
  the switch **decides** to send a pause out of that port. (Xon is the lower threshold at which it
  resumes.)
- **Headroom** is a *reservation*: separate buffer, per (port, lossless PG), that absorbs the bytes
  arriving **after** the pause decision. Those are the frame the port is already transmitting, the
  sender's in-progress frame, the bytes on the wire in both directions, and the response time:
  H = 2 × MTU + 2 × r × (L / v) + r × t_resp + 64 B.

## Symptom of undersized headroom

**Non-zero lossless-class discards** (`discards_tc3` on the switch port, or the vendor's PG/ingress
drop counter) **while PFC is active** on that port. The pause *was* sent, but too late for the bytes
already in flight. Any TC 3 discard on ORION is a page.

## Why the longest links show it first

The only term that depends on the port is **2 × r × L / v**, the bytes in flight on the cable. A
profile sized for short cables is short by exactly that term on long ones. At 400 Gb/s every extra
metre needs 2 × 50 B/ns × 5 ns = 500 B. A 5 m profile (70,996 B) is 47,500 B short on a 100 m uplink
(T1), and only 2,500 B short on a 10 m link. The 100 m leaf–spine links drop first.

**Common mistake:** "raise Xoff". That does not create headroom; it delays the pause, so even more bytes
are buffered when the in-flight bytes arrive. Lowering Xoff, or reserving more headroom, is the fix.
