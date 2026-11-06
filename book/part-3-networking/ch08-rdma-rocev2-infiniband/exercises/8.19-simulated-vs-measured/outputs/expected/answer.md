# 8.19 — Simulated versus measured conclusions (model answer)

Relies on the evidence-label rules (docs/STYLE_GUIDE.md §3), lab README §2 (realism boundary) and the
8.13 diagnosis. Each conclusion in `diagnosis.md`, classified:

| Conclusion in `diagnosis.md` | Status with `[SIMULATED]` data (today) | Status with the same pattern in `[MEASURED]` data + manifest |
|---|---|---|
| "Pair n05–n06 on rail 5 has a plateau of ≈ 202 Gb/s against a fleet median of ≈ 389 Gb/s" | A property of the generator, not of any hardware | **Observed fact** about that hardware, configuration and run set |
| "`orion-n05 mlx5_5` PCIe link is at x8 (LnkSta < LnkCap)" | Synthetic | **Observed fact** (from `lspci -vv`) |
| "The x8 link *caused* the shortfall" | Hypothesis consistent with the model | **Strongly supported**: the modeled Gen5 x8 ceiling of ≈ 200–220 Gb/s matches, and small-message rate is unchanged. But it is **proven only by a fix-and-retest**: reseat → LnkSta x16 → plateau recovers to ≈ 389 Gb/s |
| "Pair n07–n08 on rail 2 has a p99.9 tail ≈ 8.5× the fleet's" | Synthetic | Observed fact |
| "The tail comes from host jitter / PFC pauses / a marginal link" | Hypothesis | **Still a hypothesis.** Only a discriminating test promotes one cause: pinned rerun, a different rail-2 peer to localize n07 vs n08, pause and FEC counters captured in the same run window |
| "Typical latency is normal, so it is not a path/MTU issue" | Reasoning about synthetic numbers | A sound inference from observed facts (still not a root cause) |

**Key point:** in `[SIMULATED]` data **none** of these statements is a fact about hardware. The lab
tests the *analysis method*. With `[MEASURED]` data, observations become facts, but causal claims still
need a mechanism plus a test that changes only the suspected variable.
