# 10.K6 — Five DOM quantities a CMIS module reports

CMIS modules (QSFP-DD/OSFP) expose digital optical monitoring (DOM/DDM) through their memory map,
read with `ethtool -m` on hosts or the NOS's transceiver commands on switches (Section 10.7).
Values are instantaneous; the comparison is what makes them evidence.

| Quantity | Failure it helps detect | Compare against |
|---|---|---|
| Module temperature (°C) | Airflow or fan failure, blocked cage, missing blanking panel; overheating optics age fast | Neighbouring modules in the same switch, the module's high warning/alarm thresholds, the commissioning baseline |
| Supply voltage (V) | Host power-rail problem on the cage or line card | Nominal 3.3 V and the module's voltage thresholds |
| Tx bias current per lane (mA) | Laser aging: bias rises as the laser control loop compensates for lost efficiency | The lane's commissioning baseline and trend; sibling lanes |
| Tx output power per lane (dBm) | Failing laser or driver (low power on one lane) | Vendor specification and module thresholds; the far end's Rx power |
| Rx input power per lane (dBm) | Dirty or damaged connector, fiber damage or macro-bend, wrong fiber or polarity, failing far-end laser | Far-end Tx minus the designed channel loss (link budget, Section 10.6), sibling lanes (≥ 3 dB imbalance = one fiber), policy thresholds (−4.0 dBm warn, −5.9 dBm DR4 receiver minimum) |

Also acceptable: LOS/LOL flags per lane (disconnected fiber, wrong optic, polarity swap; compare with
the cabling schedule), and laser temperature/TEC current on coherent or cooled modules.

**Key point.** The module's own programmed low-Rx thresholds (≈ −6 dBm warn, −9 dBm alarm on a typical
DR4 module) sit *below* the receiver minimum and are informational, not acceptance criteria
(`[ILLUSTRATIVE]` policy, `lab/data/thresholds.yaml`).
