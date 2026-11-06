# 7.K7 — Gray failures and detection time (worked solution)

Relies on manuscript Section 7.9 ("The failure-detection ladder", Table 7.7). Timers are
configuration choices `[ILLUSTRATIVE]`; the arithmetic is `[MODELED]`.

## Definition

A **gray failure** is a partial failure where a component *looks* healthy to the usual health checks
(link state up, control plane responsive) but does not forward traffic correctly. Examples: a
unidirectional fiber (light in one direction only), an optic that corrupts or drops a fraction of
frames, a wedged forwarding pipeline whose CPU still answers. Loss of signal never fires because the
physical link stays up.

## Detection mechanism

**BFD** (Bidirectional Forwarding Detection, RFC 5880/5881) catches it. BFD sends small liveness
packets on the forwarding path of the same /31, so it detects a path that does not deliver packets,
whatever the link state says. It runs one session per BGP neighbor and tears down the BGP session
(withdrawing that ECMP member) when it declares the neighbor down.

## Detection times

- **BFD 300 ms × 3:** the session goes down after 3 consecutive missed packets:
  300 ms × 3 = **0.9 s**.
- **BGP 3 s / 9 s, no BFD:** the hold timer restarts on every keepalive received, so detection
  takes up to the hold time, **≤ 9 s**: between 6 s and 9 s after the failure, depending on where it
  falls in the 3-second keepalive cycle. A gray failure that still lets some BGP keepalives through
  may never be detected at all. That is the strongest argument for BFD.

BFD is therefore ≈ 10× faster than DC-tuned BGP timers, and ≈ 100–200× faster than default BGP hold
timers (90–180 s), which are unacceptable for AI fabrics.

## Common wrong answers

- Naming loss-of-signal as the detector: it cannot see a gray failure.
- Using 3 s (the keepalive interval) as the BGP detection time instead of the 9 s hold time.
