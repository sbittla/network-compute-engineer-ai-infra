# 8.18 — How a READY verdict can still be wrong (model answer)

Relies on manuscript Table 8.10 (lab coverage: items 1–12, with item 9 as the DSCP map only, and 16
for the login shell and Slurm job step; item 13 correlated) and docs/VERIFIED_FACTS.md (GPUDirect RDMA
validation, locked memory). The validator inspects **host captures** against a baseline, so a READY
verdict means only "nothing it checks is wrong". Any three gaps, each with an evidence source:

| Gap (false negative) | Why the validator misses it | Evidence that closes it |
|---|---|---|
| **Switch-side misconfiguration**: leaf port MTU 1500, DSCP not trusted, PFC off on priority 3, wrong ECN profile | Invisible from host captures (item 18) | Switch config compliance against intent, or switch telemetry (Fabric team API/CLI; Lab 7 validator) |
| **GPUDirect RDMA blocked** although `nvidia_peermem` is loaded: ACS redirect or IOMMU on the PCIe switch ports | PEERMEM checks only that the mechanism exists (necessary, not sufficient) | `lspci -vvv` ACSCtl on the switch ports above GPU/NIC; `ib_write_bw --use_cuda=<gpu>` per rail; NCCL `/GDRDMA` channel lines (Chapter 13) |
| **Cabled to the wrong leaf port** while IP addresses are configured correctly | Addressing matches the plan; the physical neighbour is not checked | LLDP neighbour data (`lldpctl` on the host, or the switch LLDP table) compared with the cabling plan |
| **Baseline itself is wrong**: firmware matches the site baseline but that firmware/driver pair is outside the vendor compatibility matrix | The check compares with the baseline, not with the matrix | Vendor support-matrix check in the baseline review |
| **`NCCL_IB_TC` overridden at run time** (the job script or container sets 26 although the env file says 106) | TRAFFIC_CLASS reads only the site env file (item 11) | The rank's effective environment (`/proc/<pid>/environ`, or the job's NCCL INFO log); switch per-class counters while traffic runs |
| **Locked-memory limit** finite inside the container | MEMLOCK checks the login shell and a Slurm job step, not the container runtime (item 16) | `ulimit -l` inside the container (`docker run --ulimit memlock=-1` or the runtime's default) |

A READY node must still pass **peer validation** (item 19) before admission. That is the only check
that exercises the path end to end.
