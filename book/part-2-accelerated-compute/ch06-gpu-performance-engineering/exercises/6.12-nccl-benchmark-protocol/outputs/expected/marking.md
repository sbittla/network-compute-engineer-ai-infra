# Marking scheme: 6.12 Benchmark protocol for two NCCL versions

Type outline-mandated · kind written · tier L1 · 10 points

**Evidence required:** the protocol with every control and the decision rule; manifest fields.

| Criterion | Points |
|---|---|
| Warm-up (-w) and measured iterations (-n) stated; ≥ 6 separate launches per version | 2 |
| Arms interleaved; concurrency controlled (dedicated nodes, nothing else running) | 2 |
| Input sizes swept (e.g. 8 B to 8 GiB, factor 2); only the NCCL version varies, identical topology (mapping CSV golden) and environment | 2 |
| Noise floor from an A/A comparison (same version twice) | 1 |
| Pre-registered decision rule: median busbw per size per launch, bootstrap CI over launches, practical threshold | 2 |
| Manifest fields: NCCL, driver, CUDA, NIC firmware, OFED/DOCA, topology, env vars, sizes, iteration counts | 1 |
