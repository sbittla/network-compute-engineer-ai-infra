# K5 — PUE: worked solution

Sources: manuscript Sections 21.4 and 21.6; docs/REFERENCE_CLUSTER.md (PUE 1.25 is canonical; 1.45 is
the prompt's declared hot-season variation). Inputs `[ILLUSTRATIVE]`; results `[MODELED]`.

**IT load.** 32 nodes × 8.5 kW sustained × 1.12 (fabric, storage, management) = 304.64 kW.

**Facility power = IT × PUE.**

```text
PUE 1.25:  304.64 × 1.25 = 380.8 kW   (76.2 kW of cooling and electrical overhead)
PUE 1.45:  304.64 × 1.45 = 441.7 kW   (137.1 kW of overhead)
```

The same IT work needs 60.9 kW (+16.0 %) more facility power in the hot season. The overhead itself
grows by 80 %, from 76.2 to 137.1 kW. In a power-limited site that 61 kW is headroom that is no longer
available for IT. Annual energy cost is ≈ 4 % of TCO (Section 21.4), so the cost effect is smaller
than the capacity effect.

**What PUE does not tell you** (two needed):

1. **Nothing about IT efficiency.** PUE = total facility power / IT power. A hall full of idle or
   badly scheduled GPUs can have an excellent PUE. Useful work per facility kWh (tokens per kWh,
   Section 21.5) is the efficiency metric.
2. **It varies with weather and load.** A single annual figure hides seasonal peaks (1.45 here) and
   low-load inefficiency. Capacity must be planned on the worst-case figure, not the annual average.
3. **It hides where the overhead goes.** Chiller, fans, pumps, UPS and transformer losses are lumped
   together, so PUE cannot tell you which subsystem to fix.
4. **Boundary effects.** Moving fans from the room into the servers, as liquid cooling partly does,
   shifts power into "IT" and improves PUE without saving energy.

**Common wrong answers**

- Applying PUE to a figure that already includes it, for example multiplying 380.8 kW by 1.45.
- Using provisioned 10.2 kW per node instead of the 8.5 kW sustained figure for an energy estimate.
  Provisioned power is right for capacity, sustained for energy.
- Presenting 1.45 as ORION's PUE. It is a labelled variation.
