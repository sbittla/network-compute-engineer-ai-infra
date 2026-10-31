# R4 — Most severe isolation violation: guidance and model answer

**Relies on:** Section 19.8 (RBAC, secrets, audit), Section 19.9 (Table 19.7); lab `data/tenants.yaml`,
`data/isolation_policy.yaml`; the 10 violations reported by `check_isolation()`.

## Answer

**The `cluster-admin` binding for `sa:acme-train:trainer` (acme-research, RBAC_FORBIDDEN_ROLE)** is the
most severe.

## Reasoning from blast radius

- `cluster-admin` is cluster-scoped. Any workload running as that service account can read **every
  Secret in every namespace** (other tenants' dataset tokens and model-weight credentials), schedule
  privileged pods on **any node**, mount host paths, and modify RBAC itself. It can also erase the
  evidence that would show any of this happened. One compromised training container becomes full
  platform compromise across all three tenants.
- It is also easily exercised: a service account token is mounted into every pod that uses it, so no
  human credential has to leak.

## A defensible alternative

**borealis's parent-path export `/lustre/projects` (STORAGE_OVERLAP)** gives read access to acme's and
cobalt's data directly through the file system, with no further step needed. It is read-only and limited
to storage, so it is narrower than `cluster-admin`, but it may already have exposed data. Accept either
answer when the reasoning compares the scope of access.

## How the others compare

- Shared VNI (10020) or P_Key (0x8001): these merge L2 segments or IB partitions. That gives
  reachability, and therefore an attack path, but not data access by itself.
- Secrets prefix `kv/tenants/`: broad read of secrets. This is serious, but limited to the secrets store.
- Time-slicing and no scrub: data residue, fault-sharing and performance risk.
- 30-day audit retention: loses the evidence, but grants no access.

## Response

Treat the two data-exposure violations as security incidents, not just configuration fixes. Remove the
binding, rotate every Secret readable cluster-wide, and review API audit logs for its use. Narrow the
export, then review storage access logs for reads outside `/lustre/projects/borealis`.
