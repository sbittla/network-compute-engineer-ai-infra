# 17-M3 · Pending-despite-free-GPUs troubleshooting guide (★★ · L1)

Type: outline-mandated · Kind: computed · Points: 10

<!-- prompt:start -->
**17-M3** ★★ L1 (L2 optional) — *Troubleshoot a job that is pending despite apparently free GPUs;
list scheduler, device-plugin, topology, quota, and node-health evidence.* Write a troubleshooting
guide organized by evidence source, with the exact Kubernetes and Slurm commands, what each output
proves, and the decision order. Apply it to lab cases P03 and P11 and show your reasoning.
*Evidence required:* the guide with commands per evidence class; the two applied diagnoses with the
evidence lines quoted.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the lab snapshot in [lab/data/](../../lab/data/) (seed 17).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Write the guide in `outputs/answer.md`, organised by evidence source (scheduler, device plugin, topology,
quota, node health). For each source give the exact Kubernetes and Slurm commands, what each output proves
or rules out, and where it sits in the decision order. Then apply the guide to cases P03 and P11 from
[lab/data/pending_cases.json](../../lab/data/pending_cases.json): quote the evidence lines you used and
state the diagnosis each one supports. Label any number you use.

**Hardware run (course harness).** Optional L2 evidence: `python scripts/hw_labs.py run ch17` (course
harness) shows the real-node versions of DEVICE_PLUGIN_NOT_ADVERTISING and SELECTOR_MISMATCH in
`lab/l2/results/`. Run it from the repository root. The harness builds and runs a Docker image, so Docker must be running.