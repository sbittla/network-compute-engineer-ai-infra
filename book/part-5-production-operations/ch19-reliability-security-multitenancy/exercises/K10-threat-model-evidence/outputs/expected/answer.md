# K10 — From threat model to evidence: worked solution

**Relies on:** Section 19.8, Section 19.9.2 (Tables 19.9a and 19.9b, the GPU memory sanitization
paragraph), Section 16.10 (decommissioning). Command names and Kubernetes features are
`[VENDOR-SPEC, 2026-10]`.

| Claim | Asset / threat | Mitigation | Check (Table 19.9b) | Pass condition |
|---|---|---|---|---|
| (a) A tenant pod cannot read another tenant's Secrets | Secrets / privilege escalation or cross-namespace access through RBAC | Namespaced `Role`/`RoleBinding`s; no cluster-scoped binding to tenant subjects; per-tenant secrets-manager paths; Secrets encrypted at rest (KMS) | V7: `kubectl get clusterrolebindings -o wide`; `kubectl auth can-i get secrets -n <other-ns> --as=system:serviceaccount:<ns>:<sa>` (and `-A`) | No tenant subject in any cluster binding; `no` |
| (b) A GPU passed from A to B holds none of A's data | GPU memory / residue read by the next tenant | Whole GPU or MIG across tenants; reset on tenant change | V2: A fills its allocation with a known 64-bit pattern and exits; B, as another user on the same GPU, allocates the same amount uninitialized (`torch.empty`) and counts matches | Zero matches |
| (c) A retired node's NVMe holds no tenant data | Local NVMe / data remanence after RMA or resale | NVMe Sanitize crypto or block erase (NIST SP 800-88 Purge), or destruction; per-tenant keys allow crypto-shredding | V11: `nvme id-ctrl /dev/nvmeN -H \| grep -i -A4 sanicap` before; `nvme sanitize-log /dev/nvmeN` after; lifecycle record | Erase supported (else destroy); log shows successful completion; certificate lists every serial |

**The non-read-only check.** V2 allocates and writes GPU memory as two users, so it runs only on a drained
lab node, never on a node carrying tenant work. (The sanitize in (c) is destructive too, but it is the
Section 16.10 retirement action; the check itself, `sanitize-log`, only reads.)

**What (b) cannot prove.** A pass covers the driver branch, platform, allocation size and sequence that
were tested; it is evidence, not a guarantee. Clearing behaviour is a driver property, so the test must be
rerun per driver branch, after a GPU reset and after MIG reconfiguration. It also says nothing about
reuse *within* one process: CUDA does not zero allocations and a caching allocator returns the same
process's old data, so a multi-customer inference server must isolate customers itself.

## Common wrong answers

- Citing `kubectl get secrets` as the tenant succeeding or failing from the operator's own account: the
  check must impersonate the tenant's identity (`--as`).
- Treating MIG as proof against residue across *sequential* tenants: MIG separates concurrent instances;
  clearing on reconfiguration is still a driver property to test.
- Offering `nvme sanitize` itself as the "check": it is the irreversible action; the evidence is the
  sanitize log and the certificate.
