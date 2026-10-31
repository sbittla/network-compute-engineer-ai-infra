# H1 — Progressive Lab 3: congestion telemetry diagnosis (★★, L1)

Type: Hands-on lab · kind: `lab` · 100 points

## Prompt

<!-- prompt:start -->
**H1 ★★ L1 (L3 extension) — Progressive Lab 3: congestion telemetry diagnosis.** Complete
[lab/README.md](../../lab/README.md) Tasks 1–8 until `python check.py` reports every check PASS (or SKIP), then hand-edit the
generated report into the chapter deliverable: congestion diagnosis (ranked hypotheses and
discriminating evidence per episode), experiment plan, mitigation proposal.
*Evidence required:* checker output; report (≤ 3 pages) with every section in `REPORT_SECTIONS`; the
simulation table labelled `[SIMULATED]`; a "cannot conclude" list of at least four items.
<!-- prompt:end -->

## What to submit

Complete lab Tasks 1–8 in `lab/starter/congestion_lab.py` until the checker reports every check PASS (or SKIP), then hand-edit the generated report. Put every deliverable in `outputs/`:

- `outputs/check_output.txt` (the full checker output)
- `outputs/report.md` (≤ 3 pages: diagnosis, experiment plan, mitigation proposal)

Run:

```bash
cd ../../lab && python check.py | tee ../exercises/H1-congestion-telemetry-lab/outputs/check_output.txt
```

**Hardware run (course harness).** Hardware notes on the course harness: `python scripts/hw_labs.py run
ch09` records that no RDMA NIC counters exist on that host. It runs your `counters_to_rates` on the
host's real TCP/ECN counters around a loopback N:1 incast; see `lab/l2/results/`.
