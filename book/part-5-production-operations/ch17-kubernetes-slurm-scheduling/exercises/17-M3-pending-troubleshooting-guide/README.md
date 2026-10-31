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

## What to submit

Write your working in `outputs/answer.md`: formula → substitution → result with units for every
part, with evidence labels. If you check it with a script, save it as `outputs/work.py` and run it
from this folder with `python outputs/work.py`.

**Hardware run (course harness).** Optional L2 evidence: `python scripts/hw_labs.py run ch17` (course
harness) shows the real-node versions of DEVICE_PLUGIN_NOT_ADVERTISING and SELECTOR_MISMATCH in
`lab/l2/results/`.
