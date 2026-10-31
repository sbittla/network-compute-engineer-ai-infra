# K6 — Direction of pause (worked solution)

Relies on manuscript Section 9.4 (PFC mechanics) and Section 9.8 ("Reading counters correctly").

Pause frames are link-local: they are sent by the *receiver* whose buffer is filling, to the
*transmitter* on the other end of the same cable.

- **Port P, high `pfc_tx_p3`:** P is *sending* pause frames. **P's own ingress buffer** (priority
  group for priority 3) is filling: traffic arriving on P cannot drain fast enough toward its egress.
  P is **asking its link peer** (the device upstream on that cable) **to stop sending priority 3** into P.
- **Port Q, high `pfc_rx_p3`:** Q is *receiving* pause frames. **The peer's ingress buffer** on the far
  end of Q's cable is filling. **Q is being asked to stop transmitting priority 3 out of Q**, so Q's own
  TC 3 egress queue will now back up. If the pause persists, Q's switch may in turn pause its own
  upstream ports: that is how propagation spreads.

Rule of thumb for walking a congestion tree: follow `pfc_rx` *downstream*. The congested port that is
**not** receiving pause is the root (Section 9.5, lab Task 3).

**Common mistake:** reading `pfc_tx` as "this port is paused". It is the one doing the pausing.
