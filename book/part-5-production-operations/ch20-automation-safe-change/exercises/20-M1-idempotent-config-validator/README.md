# 20-M1 — Idempotent node/network configuration validator (★★, L1)

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

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md). Values are ORION `[ILLUSTRATIVE]` unless stated.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in [`outputs/`](outputs/). Expected files:

- `outputs/validator.py` (or your IaC/config-management example)
- `outputs/fixture.json` (L1 captured state)
- `outputs/run1.jsonl`, `outputs/run2.jsonl`, `outputs/run3.jsonl`, `outputs/run4.jsonl` (audit lines of the four runs below)
- `outputs/manifest.yaml` (L2 only)

**CLI contract (the flags this exercise expects your validator to accept).** With no flags it only
validates. `--fixture <file>` reads captured state instead of the live host (L1). `--apply` plans the IP-MTU
fix but stays a dry run: it records each planned action as `dry-run` and writes nothing. `--apply --no-dry-run`
performs the fix and reads the state back. Exit codes are 0 in sync, 1 drift, 2 cannot determine.

The prompt's "two consecutive runs" are the two `--apply --no-dry-run` runs (runs 3 and 4). Runs 1 and 2 show
that validation and a plain `--apply` change nothing. Run from this exercise folder:

```bash
python outputs/validator.py --fixture outputs/fixture.json                         > outputs/run1.jsonl  # validate: exit 1 on drift
python outputs/validator.py --fixture outputs/fixture.json --apply                 > outputs/run2.jsonl  # dry run: plans 1 action, writes nothing
python outputs/validator.py --fixture outputs/fixture.json --apply --no-dry-run    > outputs/run3.jsonl  # fixes IP MTU, read-back in sync, exit 0
python outputs/validator.py --fixture outputs/fixture.json --apply --no-dry-run    > outputs/run4.jsonl  # must plan 0 actions, exit 0
```

At L1, have `--no-dry-run` write the fix back into the fixture file, so that run 4 sees the fixed state. Keep a
pristine copy of the fixture if you want to rerun from the drifted state.

**Hardware run (course harness).** The course harness cannot do the L2 run (it has no root and no netdev
besides `lo`). `python scripts/hw_labs.py run ch20` runs only a read-only `LinuxHost` adapter, which
proves a dry run writes nothing. Use a lab VM with soft-RoCE for the L2 evidence. Run it from the repository root. The harness builds and runs a Docker image, so Docker must be running.