# R1 — Deriving real acceptance thresholds

**Procedure.**
1. **Population:** run the full acceptance suite on ≥ 20 known-good nodes of the same platform and
   bundle (ideally the whole delivery, excluding nodes that failed for a known defect).
2. **Repetitions:** ≥ 5 runs per metric per node after warm-up (discard the first run), at the same
   inlet temperature band and with the same tool versions, so you separate node-to-node spread from
   run-to-run noise.
3. **Statistic:** per metric, the population median and a robust spread (IQR or the p5/p1
   percentile); also the per-node run-to-run spread. Robust statistics stop one bad node from
   moving the threshold.
4. **Margin:** FAIL below the low tail of the known-good population (e.g. median − 3 × robust spread,
   or the p1 value), WARN between that and a tighter band (e.g. median − 2 × spread). The margin must
   exceed the run-to-run spread, or healthy nodes will fail on noise.
5. **Versioning:** record thresholds in the policy file with the population, run count, date, and
   bundle; re-baseline after every bundle change (a new NCCL version shifts busbw) and per algorithm
   (NVLS vs Ring).

**Evidence class.** The resulting thresholds are `[MEASURED]` for *that* environment, not
universal; the lab's 400/330 GB/s and 360 Gb/s values are `[ILLUSTRATIVE]` teaching values (Table
16.4).

**Common mistakes:** a single run per node; using the mean (pulled down by outliers); one threshold
for both NCCL algorithms; never re-baselining. Source: Section 16.5, Table 16.4 caption.
