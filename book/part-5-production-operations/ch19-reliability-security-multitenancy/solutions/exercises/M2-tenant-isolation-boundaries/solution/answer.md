# M2 — Tenant isolation boundaries (isolation model): reference solution

**Relies on:** Section 19.8 (security foundations), Section 19.9 (Table 19.7, Figure 19.5); lab
`data/tenants.yaml`, `data/isolation_policy.yaml`, and `check_isolation()` (lab Task 6). Configuration is
`[ILLUSTRATIVE]`.

## Boundary table (three ORION-XL tenants)

Tenants: **acme-research** (training), **borealis** (training), **cobalt-inference** (inference).

| Layer | Boundary mechanism | acme-research | borealis | cobalt-inference | Pitfall the policy blocks |
|---|---|---|---|---|---|
| Identity / RBAC | SSO group → namespaced `RoleBinding`; Slurm account | `grp-acme` → `tenant-admin` in `acme-train`; SA `trainer` gets a namespaced `trainer` role only | `grp-borealis` → `borealis` | `grp-cobalt` → `cobalt-serve` | Cluster-scoped roles for tenant subjects (the lab's `cluster-admin` SA) |
| Network | Unique VRF, VNI, frontend VLAN (and IB P_Key on the IB variant) | VRF-ACME, VNI 10010, VLAN 210, P_Key 0x8001 | VRF-BOREALIS, VNI 10020, VLAN 220, P_Key 0x8002 | VRF-COBALT, VNI 10030, VLAN 230, P_Key 0x8003 | Shared VNI = shared L2 segment; shared P_Key merges partitions |
| Storage | Per-tenant fileset/export, per-tenant KMS key, no overlapping paths | `/lustre/projects/acme` rw, `kms/acme-01` | `/lustre/projects/borealis` rw, `kms/borealis-01` | `/lustre/projects/cobalt` rw, `kms/cobalt-01` | Parent-path export exposes every child tenant |
| GPU allocation | Whole GPU for training; MIG only if sharing across tenants; reset/scrub on release | whole, scrub | whole, scrub | whole (or MIG if consolidated), scrub | Time-slicing across tenants; residue in HBM |
| Secrets | Vault path ending in the tenant name; runtime injection | `kv/tenants/acme-research/` | `kv/tenants/borealis/` | `kv/tenants/cobalt-inference/` | Non-tenant prefix (`kv/tenants/`) = read-all |
| Audit | Central append-only SIEM; retention ≥ 365 days | 400 d | 400 d | 400 d | Short retention destroys the proof of isolation |

**Reachability is not performance.** VRF/VNI/P_Key separation stops cross-tenant addressing, but the
two training tenants still share spines and buffers (K8). For performance isolation, place acme and
borealis on separate leaf groups where possible and give cobalt's latency-sensitive traffic its own QoS
class. The inference tenant needs no cross-tenant GPU sharing. Whole GPUs (TP = 8 replicas) are the
default; MIG is the only acceptable sharing mode if small models are consolidated.

## Policy (machine-readable, the lab's format)

```yaml
min_audit_retention_days: 365
forbidden_roles_for_tenant_subjects: [cluster-admin]
unique_per_tenant: [vrf, vni, ib_pkey, frontend_vlan]
gpu_cross_tenant_sharing_requires: mig
scrub_on_release_required: true
secrets_prefix_must_end_with_tenant_name: true
storage_exports_must_not_overlap_other_tenants: true
```

## Tenant configuration (corrected)

```yaml
tenants:
  - name: acme-research
    idp_group: grp-acme
    k8s_namespaces: [acme-train, acme-dev]
    slurm_account: acme
    rbac_bindings:
      - {subject: "group:grp-acme", role: tenant-admin, scope: "namespace:acme-train"}
      - {subject: "sa:acme-train:trainer", role: trainer, scope: "namespace:acme-train"}
    network: {vrf: VRF-ACME, vni: 10010, ib_pkey: "0x8001", frontend_vlan: 210}
    storage:
      exports: [{path: /lustre/projects/acme, mode: rw}]
      encryption_key_id: kms/acme-01
    gpu: {allocation_mode: whole, shared_with: [], scrub_on_release: true}
    secrets: {backend: vault, path_prefix: kv/tenants/acme-research/}
    audit: {sink: siem-central, retention_days: 400}
  - name: borealis
    idp_group: grp-borealis
    k8s_namespaces: [borealis]
    slurm_account: borealis
    rbac_bindings:
      - {subject: "group:grp-borealis", role: tenant-admin, scope: "namespace:borealis"}
    network: {vrf: VRF-BOREALIS, vni: 10020, ib_pkey: "0x8002", frontend_vlan: 220}
    storage:
      exports: [{path: /lustre/projects/borealis, mode: rw}]
      encryption_key_id: kms/borealis-01
    gpu: {allocation_mode: whole, shared_with: [], scrub_on_release: true}
    secrets: {backend: vault, path_prefix: kv/tenants/borealis/}
    audit: {sink: siem-central, retention_days: 400}
  - name: cobalt-inference
    idp_group: grp-cobalt
    k8s_namespaces: [cobalt-serve]
    slurm_account: cobalt
    rbac_bindings:
      - {subject: "group:grp-cobalt", role: tenant-admin, scope: "namespace:cobalt-serve"}
    network: {vrf: VRF-COBALT, vni: 10030, ib_pkey: "0x8003", frontend_vlan: 230}
    storage:
      exports: [{path: /lustre/projects/cobalt, mode: rw}]
      encryption_key_id: kms/cobalt-01
    gpu: {allocation_mode: whole, shared_with: [], scrub_on_release: true}
    secrets: {backend: vault, path_prefix: kv/tenants/cobalt-inference/}
    audit: {sink: siem-central, retention_days: 400}
```

## Checker run

```text
>>> check_isolation(yaml.safe_load(open("tenants.yaml")), yaml.safe_load(open("isolation_policy.yaml")))
set()                                    # zero violations on the corrected config
>>> check_isolation(<lab data/tenants.yaml>, policy)   # the planted config: 10 violations
```

## The 10 planted violations and their remediation

| Tenant | Code | Remediation |
|---|---|---|
| acme-research | RBAC_FORBIDDEN_ROLE | Replace the `cluster-admin` binding of `sa:acme-train:trainer` with a namespaced role; audit for other cluster-scoped bindings |
| borealis, cobalt-inference | SHARED_VNI (×2) | Give cobalt VNI 10030; verify the EVPN fabric has no stale VNI 10020 mapping on cobalt's VTEPs |
| acme-research, cobalt-inference | SHARED_IB_PKEY (×2) | Give cobalt P_Key 0x8003; enable switch-side partition enforcement |
| borealis | STORAGE_OVERLAP | Replace the `/lustre/projects` export with `/lustre/projects/borealis`; review access logs for reads of other tenants' paths |
| cobalt-inference | GPU_SHARING_NOT_MIG | Stop time-slicing with borealis: whole GPUs, or MIG instances |
| borealis | NO_SCRUB | Enable reset/scrub on release; validate in the lifecycle (Chapter 16) |
| borealis | SECRETS_SCOPE | Narrow the prefix to `kv/tenants/borealis/`; rotate any secret readable under `kv/tenants/` |
| cobalt-inference | AUDIT_RETENTION | Raise retention from 30 to ≥ 365 days |

Two of these (the `cluster-admin` binding and the parent-path export) are data-exposure violations,
so they are also security incidents: rotate the credentials and review the access logs, not just fix
the configuration.
