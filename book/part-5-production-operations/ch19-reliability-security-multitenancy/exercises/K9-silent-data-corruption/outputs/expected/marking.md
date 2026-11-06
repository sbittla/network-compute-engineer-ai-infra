# Marking scheme: K9 Silent data corruption

Type knowledge-check · kind written · tier L1 · 5 points

**Evidence required:** why SDC evades error-based detectors; two detection methods; the restore choice with its reason

| Criterion | Points |
|---|---|
| Evasion: SDC raises no ECC/Xid/AER/link event and the collective completes, so error- and timeout-based detectors see nothing | 2 |
| Two detection methods (loss/grad-norm anomaly rule, cross-replica parameter checksum, golden-batch replay on suspect vs known-good node with bisection, dcgmi diag -r 3/4 or vendor SDC screen) | 2 |
| Restores the newest checkpoint before the anomaly onset, not the newest checkpoint, because later checkpoints may hold corrupted weights | 1 |
