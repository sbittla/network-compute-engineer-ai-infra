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

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md); reliability uses node MTBF ≈ 1,536 node-hours, repair turnaround (MTTR) 5 days and restart overhead ≈ 15 min.
- **Checking your work:** Run the lab checker as shown below; this exercise is done when the named checks pass.

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/isolation_model.md`
- `outputs/tenants.yaml`
- `outputs/isolation_policy.yaml`
- `outputs/check_isolation_run.txt`

`check_isolation()` has no command line of its own. Start from the lab's `data/tenants.yaml` and
`data/isolation_policy.yaml` (same schema; the lab's copy deliberately contains violations), write your own
versions into `outputs/`, then implement Task 6 in `lab/starter/incident_toolkit.py` and run it on your files:

```bash
cd ../../lab
python -c "import sys, yaml; sys.path.insert(0, 'starter'); from incident_toolkit import check_isolation; t = yaml.safe_load(open(sys.argv[1], encoding='utf-8')); p = yaml.safe_load(open(sys.argv[2], encoding='utf-8')); v = sorted(check_isolation(t, p)); print(len(v), 'violations'); [print(*x) for x in v]" ../exercises/M2-tenant-isolation-boundaries/outputs/tenants.yaml ../exercises/M2-tenant-isolation-boundaries/outputs/isolation_policy.yaml > ../exercises/M2-tenant-isolation-boundaries/outputs/check_isolation_run.txt
```

The file should read `0 violations`. On the lab's own data the same command lists one `tenant CODE` line per
violation, which is a quick way to test your implementation against the `T6` check.
