# K3 — ECN codepoints and WRED (worked solution)

Relies on manuscript Section 9.3 ("ECN and WRED: marking before it hurts", Figure 9.2) and the ORION
class plan (DSCP 26 → TC 3 lossless).

## The four codepoints (the two low-order bits of the IP TOS / traffic-class byte, RFC 3168)

| Codepoint | Bits | Meaning |
|---|---|---|
| Not-ECT | `00` | Sender is not ECN-capable |
| ECT(1) | `01` | ECN-capable transport |
| ECT(0) | `10` | ECN-capable transport (what RoCE NICs normally send) |
| CE | `11` | Congestion Experienced: set by a *switch* |

## Behaviour above Kmin on a queue with both WRED and ECN enabled

The RED profile computes a probability p(q) that rises from 0 at Kmin to Pmax at Kmax (and is 1 above
Kmax).
- **ECT packet** (ECT(0) or ECT(1)): **marked CE** with probability p(q) and forwarded. Nothing is
  lost; the receiver NIC (NP) turns the mark into a CNP.
- **Not-ECT packet:** cannot be marked, so WRED **drops** it with the same probability p(q).

## Why the second behaviour must never occur in TC 3

TC 3 is the class ORION promises is **lossless**. A WRED drop there is a lost RoCE packet. With
go-back-N RC it triggers a NAK and retransmission of the whole in-flight window. A lost tail costs a
full ACK timeout (1–4 s, Chapter 8). PFC cannot prevent it, because the drop is a policy decision, not
buffer overflow. Therefore **all RoCE data must be sent ECT** (`NCCL_IB_TC=106` = DSCP 26 + ECT(0)), and
**WRED drop must be disabled** for the lossless class (ECN marking only).

**Common mistake:** claiming the receiver sets CE (it reflects congestion back in a CNP; only switches
set CE).
