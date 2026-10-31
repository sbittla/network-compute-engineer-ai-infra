# 5.3 — The HCA index is not the rail number (model answer)

Relies on manuscript Section 5.6.1 (NIC legend), Section 5.6.4 (cross-checking sources) and Section 5.8.

**Why `NIC1` is `mlx5_0`.** `nvidia-smi topo -m` numbers its NIC *columns* in PCI bus order. On `orion-n01` the
frontend NIC sits at bus `0d` (`mlx5_8`), below the first backend NIC at bus `19` (`mlx5_0`), so it becomes
`NIC0` and every backend NIC shifts by one; the socket-1 frontend NIC (`mlx5_9`) likewise becomes `NIC5`
`[SIMULATED]`. RDMA device names are a separate namespace, assigned by the kernel driver and udev rules in
probe order or by site naming rules (ORION pins `mlx5_i` to rail *i* by rule). So the column index, the
`mlx5_*` name and the rail are three different things; any agreement between them is a convention.

**Which source is authoritative for the rail.** Neither a column index nor a device name is evidence of where
a cable goes. The rail is a fact about the cable: read the **LLDP neighbour** of each netdev (the leaf switch
name, `orion-be-leaf-rR`, gives rail *R*) and cross-check it against the **cabling database**. Map name →
netdev with `ibdev2netdev`, then netdev → LLDP neighbour. Lab 5's `orion-n23` shows why: its cards carry the
right names, but the rail-4 and rail-5 cables are swapped at the patch panel, which only LLDP reveals.

**Common wrong answer.** "NIC1 = rail 1" or "`mlx5_0` must be rail 0 because of the naming rule" (a rule
names the card, it does not route the cable).
