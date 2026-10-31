# 10.W1 — Link budget for a cross-hall DR4 link

Inputs (prompt, `[ILLUSTRATIVE]` loss coefficients; DR4 limits `[VENDOR-SPEC, 2026-10]`, IEEE
802.3bs, verify): 420 m SMF at 0.4 dB/km, 4 mated MPO pairs at 0.5 dB, 2 splices at 0.1 dB, worst-case
Tx −2.9 dBm per lane, receiver minimum −5.9 dBm per lane, maximum channel insertion loss 3.0 dB.
Method: Section 10.6.2. Losses in dB add; a power in dBm minus a loss in dB is a power in dBm; dBm
values are never added to each other.

**(a) Channel loss, worst-case Rx power, margin** `[MODELED]`

```text
fiber      = 0.420 km × 0.4 dB/km = 0.168 dB
connectors = 4 × 0.5 dB           = 2.000 dB
splices    = 2 × 0.1 dB           = 0.200 dB
channel    = 0.168 + 2.000 + 0.200 = 2.368 dB ≈ 2.37 dB   (≤ 3.0 dB: within budget)
Rx_worst   = Tx_min − channel = −2.9 dBm − 2.368 dB = −5.268 dBm ≈ −5.27 dBm
margin     = Rx_worst − Rx_min = −5.268 − (−5.9) = 0.632 dB ≈ 0.63 dB
```

Connectors dominate (2.0 of 2.37 dB); the 420 m of fiber costs only 0.17 dB.

**(b) One dirty MPO pair adds 1.0 dB**

```text
channel = 2.368 + 1.0 = 3.368 dB > 3.0 dB      → fails the channel budget by 0.37 dB
Rx_worst = −2.9 − 3.368 = −6.268 dBm < −5.9 dBm → 0.37 dB below the receiver minimum
```

Decision: **do not accept the link**; clean (or re-terminate) and re-measure before it enters
service. A typical module (Tx ≈ +0.5 dBm) would still link at ≈ −2.87 dBm, which is exactly why
such links pass at install and fail later as lasers age toward worst-case Tx.

**(c) Rx power of (a) in mW**

```text
P(mW) = 10^(dBm/10) = 10^(−5.268/10) = 10^(−0.5268) = 0.297 mW
```

**(d) In service: Rx −4.1 dBm on all lanes, far-end Tx +0.6 dBm on all lanes**

```text
measured loss = Tx − Rx = 0.6 − (−4.1) = 4.7 dB
excess        = measured − designed = 4.7 − 2.368 = 2.33 dB (same on every lane)
```

Decision: the excess is equal on all four lanes, so the cause is an element **shared by all fibers**:
most likely a dirty or damaged MPO end-face at one of the four mated pairs (an MPO carries all eight
fibers), less likely a bad splice or a macro-bend in the trunk. Drain the link first (Section 10.12
safe-change rules), then inspect both module-side jumpers and each patch-panel interface, starting
with the most recently touched; if all end-faces pass IEC 61300-3-35, test the trunk with a loss test
set or OTDR. A single-lane loss would instead point at one fiber (Table 10.5).

**Common wrong answers.** Adding dBm values (−2.9 + −5.9); forgetting the splices (2.17 dB);
accepting (b) because "typical Tx works"; computing loss as Rx − Tx (negative); using 0.4 dB/m.
