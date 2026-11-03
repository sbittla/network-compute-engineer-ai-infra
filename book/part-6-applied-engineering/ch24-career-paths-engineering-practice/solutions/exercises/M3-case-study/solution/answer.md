# M3 — Case study: marking notes and reference

Scored out of 15 (key). Structure: Table 24.14 (Section 24.8); the exemplar "Rail misalignment after a
motherboard replacement" is the reference standard.

**Required sections (Table 24.14):** context (with *your* role); symptom and impact; evidence; ranked
hypotheses; discriminating tests; root cause as a mechanism; change and validation with repetitions;
remaining uncertainty; what changed systemically. Missing any one costs a section mark.

**Impact arithmetic, checked against the exemplar** (`[ILLUSTRATIVE]`): p50 2.10 → 2.29 s (+9.0 %);
throughput loss 1 − 2.10 / 2.29 = 8.3 %; 0.083 × 128 GPUs × 144 h ≈ 1,530 GPU-hours; × $3.00 ≈ $4,590. Learners'
own cases need the same chain: a baseline, the changed metric, a throughput fraction, GPUs × hours, and a
label on each number.

**Discriminating test.** It must be one that could have disproved a hypothesis. In the exemplar,
`ib_write_bw` from GPU0's memory through each NIC: 46 GB/s via the `PIX`-adjacent NIC vs 27 GB/s through the
NIC in use, with clean link counters and nominal clocks, rejecting the link and thermal hypotheses.
"Reran the job and it was still slow" is not discriminating.

**Remaining uncertainty and systemic change.** For example "we have not proven why enumeration changed" and
"acceptance now fails any node whose GPU *i* is not `PIX`-adjacent to NIC *i*". "Be more careful" earns
nothing.

**Anonymisation.** State what was changed: hostnames mapped onto ORION, numbers scaled, cost rate replaced
with the book's ≈ $3.00 per GPU-hour (Chapter 21 TCO, `[MODELED]`), no customer names or unreleased hardware (Section 24.8 pitfall). Deduct
heavily for confidential detail or unlabelled numbers. Length limit ≤ 800 words.
