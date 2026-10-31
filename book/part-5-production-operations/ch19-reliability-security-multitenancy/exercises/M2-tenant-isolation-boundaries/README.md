# M2 — Tenant isolation boundaries (isolation model) (★★, L1)

Type: Outline-mandated · Kind: `lab` · Points: 15

## Prompt

<!-- prompt:start -->
**M2 ★★ L1 — Tenant isolation boundaries.** Define isolation boundaries for **identity, network,
storage, GPU allocation, secrets, and audit logs** for three ORION-XL tenants (two training, one
inference). *(Deliverable: isolation model.)* Express the policy machine-readably and check it with the
lab's `check_isolation()`.
*Evidence required:* boundary table; policy YAML; checker run showing zero violations on your config.
<!-- prompt:end -->

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/isolation_model.md`
- `outputs/tenants.yaml`
- `outputs/isolation_policy.yaml`
- `outputs/check_isolation_run.txt`
