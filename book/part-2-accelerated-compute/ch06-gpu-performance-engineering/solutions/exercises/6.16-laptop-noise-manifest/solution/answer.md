# 6.16 — A 10–20 % spread on the laptop harness (model answer, 3 points)

Relies on manuscript Section 6.8 (harnesses and manifests) and Lab 6 Task 2.

Manifest fields to inspect first: **CPU frequency scaling and turbo** (governor, boost bursts that decay under
sustained load); **thermal state** (a fan-limited laptop throttles minutes into a run); **power mode** (battery
vs AC, OS power plan); **background processes** (browser, indexing, updates competing for cores); **BLAS
threading** (`OMP_NUM_THREADS`, MKL/OpenBLAS threads oversubscribing cores); **memory pressure** (swap or page
cache eviction). Each changes from one process to the next, so it shows up as run-to-run spread rather than
within-run noise.

This does not invalidate the supplied GPU analysis: that is a different system (an ORION GPU) with its own
measured A/A floor (0.66 %), and its decisions are made relative to that floor. The laptop spread only
demonstrates why the protocol (fresh processes, A/A floor, manifest) is necessary.

(≈ 140 words.)
