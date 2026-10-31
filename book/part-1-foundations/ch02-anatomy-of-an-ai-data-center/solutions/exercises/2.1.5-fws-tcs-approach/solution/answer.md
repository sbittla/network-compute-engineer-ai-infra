# 2.1.5 — FWS, TCS and approach temperature

Source: manuscript Section 2.7 ("Direct-to-chip liquid cooling") and Section 2.12 (the afternoon
slowdown).

- **FWS (facility water system):** the building's primary water loop, cooled by towers, dry coolers or
  chillers. Its water never touches IT equipment.
- **TCS (technology cooling system):** the clean, filtered, chemically controlled secondary loop that the
  CDU pumps through the rack manifolds and the cold plates on the GPUs and CPUs.
- **Approach temperature:** TCS supply temperature minus FWS supply temperature at the CDU's heat
  exchanger: the temperature "cost" of the heat exchanger at its current load and flow.

**How a hot afternoon slows a liquid-cooled GPU:** dry coolers and towers reject heat to outside air, so
FWS supply temperature rises with the ambient temperature. The CDU's approach stays roughly constant, so
TCS supply rises by about the same amount (for example from 30 °C to 34 °C). Cold plates and dies run
correspondingly warmer, and a GPU that had little thermal headroom (a poor thermal-interface contact, a
partly blocked cold plate, low flow on its branch) crosses its slowdown threshold. Its clocks drop, and in
a synchronous job every other GPU waits for it. The signature is time-of-day correlation, thermal
clock-event reasons on a few GPUs, and rising TCS supply temperature in the CDU telemetry.
