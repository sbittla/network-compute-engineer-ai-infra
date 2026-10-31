# 10.K4 — CRC stomping

**Mechanism (Section 10.2.4).** A cut-through switch starts transmitting a frame on the egress port
as soon as it has read the header, long before the frame's last bytes — and its FCS — have arrived
on the ingress port. If the FCS then turns out to be bad (the frame was corrupted on the ingress
link), the switch cannot recall the bytes it has already sent. Instead it "stomps" the outgoing
CRC: it writes a known-bad (often inverted) FCS so that the next device is guaranteed to drop the
frame rather than deliver corrupted data.

**Why a perfectly healthy link shows FCS errors.** The next hop receives a frame whose FCS fails and
counts an FCS error on *its* ingress port. That link's own physical layer is clean: pre-FEC BER is
normal, symbol errors are ≈ 0, FEC-uncorrectable is 0. FCS errors without any uncorrectables and with
a clean BER are therefore the stomping signature (discriminating question 3 of Section 10.8.1). In a
cut-through fabric a single bad link can spray FCS errors across many downstream ports.

**Localizing counter.** **FEC-uncorrectable codewords (with elevated symbol errors / pre-FEC BER) on
the ingress port of the upstream switch** where the corruption entered. Uncorrectables are produced
by the PCS of the link that actually corrupted the bits and do not propagate. Some platforms also
expose a separate "stomped CRC" (or "CRC stomped / forwarded bad") counter that identifies frames
forwarded already bad.

**Operational consequence.** Do not clean or replace the cable of the port that shows only FCS
errors; walk one hop upstream and find the port with uncorrectables (Exercise 10.M2, port P3).

**Common wrong answer.** Treating every FCS error as a local cable fault; or saying that
store-and-forward switches also stomp (they drop the bad frame at the ingress and count it there).
