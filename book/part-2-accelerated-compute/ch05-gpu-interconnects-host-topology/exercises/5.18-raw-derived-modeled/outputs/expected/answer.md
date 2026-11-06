# 5.18 — Raw, derived and modeled lab results (model answer)

Relies on manuscript Section 5.6.3, Section 5.9 and the lab's evidence labels.

**Raw observations:** the capture files themselves (`nvidia-smi_topo_m.txt`, `lstopo.txt`, `lspci_vmm.txt`,
`ibdev2netdev.txt`, `lldp.txt`, `gdr_prereqs.txt`, `gpu_inventory.csv`), labelled `[SIMULATED]` in the lab.

**Derived:** everything computed deterministically from them: lstopo-derived PIX…SYS relations (cross-checked
on 160 GPU–NIC pairs), the mapping CSV rows (29 of 32 aligned), rails from LLDP and the findings
(`RAIL_MISMATCH`, `ACS_REDIRECT`, …).

**Modeled:** the scenario table (Table 5.5: S1 352.3 GB/s … S4@SYS 186.0 GB/s), produced by the Section 5.9
model with `[ILLUSTRATIVE]` Table 5.4 parameters.

**To make the modeled ones measured:** run nccl-tests on L3 hardware for each scenario (aligned, misaligned,
with the flawed nodes) with a manifest, ≥ 5 launches per configuration, median and spread; then recalibrate
`path_model.yaml` from the measurements and label those results `[MEASURED]`.

(≈ 140 words.)
