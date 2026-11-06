# Exercise 3.12 — Host inventory and diagnostic snapshot

**Difficulty:** ★ · **Tier:** L1 · **Type:** outline-mandated · **Kind:** computed · **Points:** 10

## Prompt

<!-- prompt:start -->
Use `lscpu`, `numactl`, `free`, `vmstat`, `iostat`, `ip`, `ethtool`, `lspci` and `dmesg` to build a
**host inventory and diagnostic snapshot**.
- **L1 path:** from `orion-n01.json` (the reference node), produce a one-page inventory table: CPU
  model and topology, NUMA nodes with CPU lists and memory, GPU and NIC BDFs with NUMA node and link
  state, interface names with MTU and speed, NVMe devices, kernel and driver versions visible in the
  snapshot. Mark each value with the section it came from.
- **L2 path:** run your collector on a Linux host you are authorized to inspect (a workstation or cloud
  VM is fine), once as an unprivileged user and once as root if permitted. Produce the same table and
  list which fields were missing without root and which unprivileged fallback (if any) recovered them.
*Evidence required:* the inventory table with provenance per value; for L2, both raw JSON snapshots
and the gap comparison.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put every deliverable in [`outputs/`](outputs/):

- `outputs/inventory.md`: the inventory table with the source section for every value
- `outputs/l2_user/`: L2 path only: raw JSON snapshot and report collected unprivileged
- `outputs/l2_root/`: L2 path only: the same, collected as root (if permitted)
- `outputs/gaps.md`: L2 path only: fields missing without root and the fallback that recovered them

Command to run (from this folder):

```bash
python ../../lab/starter/host_collector.py --out-dir outputs/l2_user --note "inventory, unprivileged"   # L2 path; rerun as root into outputs/l2_root
```

Label every number (`[MEASURED]`, `[MODELED]`, `[SIMULATED]` or `[ILLUSTRATIVE]`) and show formula, substitution and result with units. Quote raw snapshot lines where you rely on them.

**Hardware run (L2 extension, optional):** from the repository root, `python scripts/hw_labs.py run ch03 --device gpu` (or `--device cpu`; the CPU fallback is automatic without a GPU) writes `lab/l2/results/<label>/report.md`. You may cite its `[MEASURED]` tables in your deliverables; say which host it ran on. The harness builds and runs a Docker image, so Docker must be running.