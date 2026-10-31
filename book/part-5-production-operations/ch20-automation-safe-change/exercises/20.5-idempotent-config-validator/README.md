# 20.5 — Idempotent node/network configuration validator (★★, L1)

Type: Outline-mandated · Kind: `computed` · Points: 10

## Prompt

<!-- prompt:start -->
Write an idempotent script, or an IaC/configuration-management example, that **validates** an
ORION node's backend network configuration against desired state and reports drift without
changing anything. Check, per backend NIC: IP MTU 9,000; RDMA active MTU 4,096; NIC firmware in
the approved list; link up at 400 Gb/s. Then add a `--apply` mode that fixes *only* the IP MTU, is
dry-run by default, and is a provable no-op on the second run.

Requirements:

- Read state through machine-readable interfaces where possible (`ip -j link show`,
  `ethtool -i <netdev>` for firmware, `ibv_devinfo` for `active_mtu`, link speed from
  `/sys/class/net/<netdev>/speed` or `ethtool <netdev>`).
- Exit code 0 = in sync, 1 = drift found, 2 = cannot determine (unreachable, missing tool).
- Emit one JSON audit line per check and per action (target, key, before, after, result).
- L1: run against a captured JSON fixture you create. L2: run on a lab VM (soft-RoCE acceptable).

**Evidence required:** source code; two consecutive runs showing drift → fixed → in sync (second
apply plans zero actions); the audit lines; for L2, the manifest fields from the lab README.
<!-- prompt:end -->

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/validator.py` (or your IaC/config-management example)
- `outputs/fixture.json` (L1 captured state)
- `outputs/run1.jsonl, run2.jsonl, run3.jsonl` (validate, apply, re-apply audit lines)
- `outputs/manifest.yaml` (L2 only)

Run:

```bash
python validator.py --fixture outputs/fixture.json            # validate (exit 1 on drift)
python validator.py --fixture outputs/fixture.json --apply --no-dry-run
python validator.py --fixture outputs/fixture.json --apply --no-dry-run   # must plan 0 actions
```
