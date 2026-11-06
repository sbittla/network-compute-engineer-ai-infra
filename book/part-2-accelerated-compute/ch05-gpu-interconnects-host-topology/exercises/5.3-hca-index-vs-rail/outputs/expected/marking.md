# Marking scheme: 5.3 HCA index is not the rail

Type knowledge-check · kind written · tier L1 · 3 points

**Evidence required:** column-order explanation; naming-rule explanation; LLDP/cabling database.

| Criterion | Points |
|---|---|
| In the capture the NIC columns follow PCI enumeration order (frontend mlx5_8 at bus 0d is NIC0); read the NIC Legend rather than assume an order | 1 |
| RDMA device names are software labels from kernel/udev naming rules (ORION names from the asset database record); neither a column index nor a name says where a cable goes | 1 |
| Authoritative source: LLDP neighbour (orion-be-leaf-rR) cross-checked against the cabling database | 1 |
