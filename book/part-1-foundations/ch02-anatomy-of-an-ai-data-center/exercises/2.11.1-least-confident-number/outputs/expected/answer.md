# 2.11.1 — The least confident number in Section 2.10

Model answer (one defensible choice; others are accepted with the same structure). The number I trust
least is the **75 % liquid capture fraction**. It is a property of the cold-plate design, the fan curve
and the inlet temperature, not of the rack, and the vendor value is quoted at a test condition that may
not match the hall. It drives three results at once: the 46.4 L/min of coolant per rack, the 10.25 kW of
residual air heat (against the room's 12 kW limit), and the CDU's 82 % load. At 0.70, air heat rises to
12.3 kW per rack and exceeds the room's limit. To replace it, run an **L3** measurement in the lab hall
with Facilities sign-off: burn in one rack (`dcgmproftester` or an approved burn-in at the default power
limit) and record rack IT power from the PDUs, TCS flow and supply/return temperatures from the CDU
(heat to liquid = ṁ × cp × ΔT), for 30 minutes after warm-up, three repetitions. The capture fraction is
liquid heat divided by IT power, labelled `[MEASURED]`. Equally good answers name the 10 % transient
margin (measure step-load swings with high-rate PDU metering, L3) or the 10.2 kW node maximum (BMC
`ipmitool dcmi power reading` under burn-in, L2).
