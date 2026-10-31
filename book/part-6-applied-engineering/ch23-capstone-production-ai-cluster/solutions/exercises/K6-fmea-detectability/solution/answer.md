# K6 — FMEA detectability (D) and why it favours "only slower" failures

**Source:** manuscript Section 23.5 ("Scoring and prioritizing: FMEA-lite"); key K6.

**Definition.** FMEA (IEC 60812) scores each failure mode 1–10 on severity S, occurrence O and
detectability D, and ranks by RPN = S × O × D. D is scored *high when the failure is hard to detect*:
D = 1 means impossible to miss, D = 10 means it will almost certainly go unnoticed until it has done
damage.

**Why a high D increases priority.** Because D multiplies the score, a quiet failure mode with modest
severity can outrank a loud, severe one. That is intentional: a loud failure (a rack power loss) is
noticed in seconds and fixed, so its cost is bounded. A quiet failure keeps costing until someone
finds it.

**Why that favours "only slower" failures.** Failures that degrade rather than break — a NIC firmware
mismatch after a partial upgrade, GPUDirect RDMA disabled on one node, a PCIe link trained at reduced
width — raise no alarm. Every synchronous job that lands on the affected node runs at the pace of
the slowest participant, silently wasting goodput across many jobs for weeks. The investment that
retires them is detection (an acceptance gate or a fleet consistency check), which is usually cheap.

**ORION example** `[ILLUSTRATIVE]` (Section 23.5):

| Failure mode | S | O | D | RPN |
|---|---|---|---|---|
| Silent NIC-firmware mismatch after a partial upgrade | 6 | 4 | 8 | 6 × 4 × 8 = **192** |
| Rack power loss | 7 | 2 | 1 | 7 × 2 × 1 = **14** |

The firmware mismatch gets the backlog item: a fleet-wide firmware consistency gate before job start
(Chapter 16; Table 23.10 scores it 1.20).

**Common wrong answers.** Defining D as "probability of detection" with high = good (inverted
scale); arguing that slow failures matter less because nothing is down; computing RPN as a sum.
