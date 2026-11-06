# 7.R3 — The single-ping troubleshooting rule (model answer)

Relies on manuscript Section 7.12 (E3 "The ping that lies", E4 path sweep) and Section 7.6
("Per-flow hashing").

## The rule (two sentences)

"A single successful probe proves exactly one ECMP path, so it can never rule out a path-dependent
fault such as an MTU mismatch on one member link. Before closing an MTU or path hypothesis, sweep at
least 4N full-size flows (N = ECMP width at the first hop) that vary the source port, and record how
many fail."

For the Section 7.12 frontend leaf (N = 16 uplinks) that means ≥ 64 full-size connections, which is
exactly the sweep that found 4 of 64 stalling.

## The ECMP reason

Switches hash each packet's header fields (the 5-tuple) and send every packet of a flow over the same
member link. A ping has no ports, so all its packets share one hash and take **one** of the N paths,
here 1 of 16. In Section 7.12 the full-size ping happened to hash onto one of the 15 good uplinks, so it
succeeded while 1/16 of TCP connections blackholed on the uplink with MTU 1500. Varying the source
port gives each probe an independent hash. With 4N probes the chance of never hitting one specific bad
member is (1 − 1/N)^(4N) = (15/16)⁶⁴ ≈ 1.6 % (≈ e⁻⁴) `[MODELED]`; with one ping it is (N − 1)/N = 94 %.

**Common mistake:** a rule that says "ping with a bigger size" without varying the flow; size alone
still tests one path.
