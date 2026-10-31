# 4.17 — Calibrating the gap classifier (model answer)

Relies on manuscript Section 4.11 (gap-attribution rule) and the lab's `find_gaps` contract.

**10 µs launch-latency allowance.** A gap is called `dependency` when the next activity was submitted more
than 10 µs before the gap began. On a host whose submit-to-start latency is longer (busy driver thread,
virtualization, MPS), ordinary launch latency exceeds 10 µs and launch-bound gaps are mislabelled as
dependencies; on a fast host, a genuine short event wait under 10 µs is mislabelled as launch-bound.

**2 µs gap threshold.** On a fast GPU with ≈ 1 µs inter-kernel spacing a real launch-bound comb can sit just
under 2 µs and be dropped; on a slower platform normal back-to-back spacing above 2 µs is counted as idle.

**Calibration.** On a known-good trace of the same platform: histogram inter-kernel gaps in a GPU-bound
region (large GEMMs back to back) and set the threshold above its p99; measure submit-to-start latency on an
idle stream (many tiny launches) and set the allowance above its p99. Record both in the manifest.

(≈ 150 words.)
