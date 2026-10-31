# 10.K1 — Pipeline stage of each counter

**Method.** Follow a frame up the receive path of Figure 10.1 (Section 10.2.2): the optical module
(PMD) turns light into an electrical signal and measures it; the SerDes recovers PAM4 symbols; the
PCS/FEC sublayer decodes RS(544,514) codewords; the MAC checks the Ethernet frame (FCS, length); the
forwarding pipeline and the traffic manager (MMU, shared buffer) decide where the packet goes and
whether it can be queued. Each counter is produced by the stage that has the information to count it.

| Counter | Stage | Justification |
|---|---|---|
| (a) Rx optical power | PMD / transceiver module (DOM) | The module's photodiode monitor measures average received power per lane; the ASIC never sees light. |
| (b) FEC-uncorrectable codewords | PCS/FEC | The RS decoder found more than t = 15 bad 10-bit symbols in a 544-symbol codeword and could not repair it. |
| (c) FCS errors | MAC | The CRC-32 over the reassembled frame does not match the frame check sequence. |
| (d) Output discards | Traffic manager (MMU) | Queue or shared-buffer admission on the egress port rejected the packet. |
| (e) PFC pause frames sent | MMU decides, MAC control sends | An ingress priority group crossed its XOFF threshold in the buffer (MMU); the MAC control sublayer emits the 802.1Qbb pause frame. |
| (f) Oversize (giant) frames | MAC | The frame is longer than the port's configured MTU; only the MAC knows the frame length against port config. |

**Common wrong answers.**

- Placing FCS errors at the PCS. The PCS works on 66b/257b blocks and FEC codewords; it has no
  notion of an Ethernet frame. A corrupted codeword the FEC cannot repair *causes* an FCS error one
  stage later, which is why the two often rise together (Section 10.8).
- Putting PFC entirely in the MAC. The MAC only transmits the frame; the decision is a buffer
  threshold, which is why PFC belongs with congestion, not with the physical layer (Chapter 9).
- Putting giants in the forwarding pipeline: it is a length check at the MAC against the port MTU,
  and it is a configuration signature (Chapter 7), not corruption.
