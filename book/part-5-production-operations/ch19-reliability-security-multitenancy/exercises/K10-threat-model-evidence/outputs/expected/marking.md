# Marking scheme: K10 From threat model to evidence

Type knowledge-check · kind written · tier L1 · 6 points

**Evidence required:** a three-row table (claim, mitigation, check, pass condition); one paragraph on the non-read-only check and the limits of (b)

| Criterion | Points |
|---|---|
| (a) Secrets: namespaced RBAC, no cluster binding to tenant subjects, per-tenant secret paths; check with kubectl auth can-i (--as the tenant service account) and the cluster-binding listing; pass = no | 2 |
| (b) GPU residue: whole GPU or MIG plus reset on tenant change; residue test with an uninitialized allocation by a second user; pass = zero pattern matches | 1 |
| (c) NVMe: Section 16.10 sanitize (crypto or block erase) or key destruction; check sanicap before and sanitize-log after, plus a certificate listing every drive serial | 1 |
| Names the residue test as the non-read-only check and confines it to a drained lab node | 1 |
| Limits of (b): a passing test covers only the tested driver branch, sequence and allocation pattern; it says nothing about reuse within one process (CUDA does not zero allocations), so rerun it per driver branch, after reset and after MIG reconfiguration | 1 |
