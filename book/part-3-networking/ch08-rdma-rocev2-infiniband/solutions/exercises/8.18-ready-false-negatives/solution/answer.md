# 8.18 — How a READY verdict can still be wrong (model answer)

Relies on manuscript Table 8.10 (lab coverage: items 1–10, with item 9 as the DSCP map only, and 12;
item 13 correlated) and docs/VERIFIED_FACTS.md (GPUDirect RDMA validation, locked memory). The
validator inspects **host captures** against a baseline, so a READY verdict means only "nothing it
checks is wrong". Any three gaps, each with an evidence source:

| Gap (false negative) | Why the validator misses it | Evidence that closes it |
|---|---|---|
| **Switch-side misconfiguration**: leaf port MTU 1500, DSCP not trusted, PFC off on priority 3, wrong ECN profile | Invisible from host captures (item 18) | Switch config compliance against intent, or switch telemetry (Fabric team API/CLI; Lab 7 validator) |
| **GPUDirect RDMA blocked** although `nvidia_peermem` is loaded: ACS redirect or IOMMU on the PCIe switch ports | PEERMEM checks only that the mechanism exists (necessary, not sufficient) | `lspci -vvv` ACSCtl on the switch ports above GPU/NIC; `ib_write_bw --use_cuda=<gpu>` per rail; NCCL `/GDRDMA` channel lines (Chapter 13) |
| **Cabled to the wrong leaf port** while IP addresses are configured correctly | Addressing matches the plan; the physical neighbour is not checked | LLDP neighbour data (`lldpctl` on the host, or the switch LLDP table) compared with the cabling plan |
| **Baseline itself is wrong**: firmware matches the site baseline but that firmware/driver pair is outside the vendor compatibility matrix | The check compares with the baseline, not with the matrix | Vendor support-matrix check in the baseline review |
| **`NCCL_IB_TC` wrong** (for example 26 instead of 106) | Not checked by the lab (item 11) | Inspect the env file; switch per-class counters while traffic runs |
| **Locked-memory limit** finite inside Slurm or the container | Not checked (item 16) | `srun bash -c 'ulimit -l'` and the same inside the container |

A READY node must still pass **peer validation** (item 19) before admission. That is the only check
that exercises the path end to end.
