# 3.14 — What the `[SIMULATED]` snapshots cannot reveal

Source: lab `README.md` Section 2 (realism boundary) and manuscript "Realism boundaries".

1. **Output formats differ on real hosts.** pciutils versions print `(ok)`/`(downgraded)` differently or
   not at all, sysstat adds or reorders columns, `mpstat` prints 12-hour timestamps without `LC_ALL=C`,
   and vendor `ethtool` output varies. Parsers tuned to one generator can silently mis-parse.
   *Validate:* run the parsers on real captures from every OS image and tool version in the fleet, and
   add those captures as regression fixtures.
2. **Real faults are intermittent.** AER storms come in bursts, a thermal throttle appears only under the
   afternoon load, and a flapping link may be up when the snapshot runs. One snapshot can miss them.
   *Validate:* collect repeatedly (or on triggers) and correlate with continuous exporter metrics before
   declaring a node healthy.
3. **Thresholds and topology are judgment, not fleet data.** The baseline's thresholds (10 corrected AER
   per BDF, 25 % NUMA-remote) and the `rail*`/`fe*` naming assume ORION. A real fleet has different noise
   floors and interface names. *Validate:* compute per-metric distributions across the fleet in shadow
   mode before enforcing, and generate the baseline from a known-good node of each hardware SKU.

Also acceptable: privilege and container effects (a collector in a container sees a different `/proc` or
cgroup view), and timing effects (the collector's own load perturbing what it measures).
