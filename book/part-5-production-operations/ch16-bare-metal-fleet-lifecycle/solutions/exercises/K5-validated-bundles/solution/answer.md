# K5 — Why validated bundles beat pairwise tables

**Combinatorial argument.** With *c* coupled components, each with *v* candidate versions, a
pairwise "A works with B" table needs C(c, 2) · v² cells. For the lab's 7 components with 3
versions each that is 21 × 9 = 189 cells `[MODELED]`, and the full space is v^c = 3⁷ = 2,187
combinations. Even a complete pairwise table says nothing about behaviour that appears only when
three or more components meet, and a node is always running *all* of them at once. A validated
bundle names one complete combination of every component and qualifies it as a unit (pilot
nodes, burn-in, representative workloads), plus a blocked list for known-bad versions. The fleet
then has one or two bundles to reason about, and compliance is an exact match (`check_compat`
returns `OK`, `DEPRECATED`, `OFF_MATRIX`, or `BLOCKED`).

**A three-way interaction a pairwise table can miss (Table 16.5):**
- **GPU driver + Fabric Manager + NVSwitch firmware.** Fabric Manager must equal the driver version
  exactly, and the NVSwitch firmware must be qualified for that branch; the NVLink fabric
  initializes only when all three agree. Each pair can look "supported" while the triple leaves
  the fabric uninitialized and CUDA applications fail to start.
- (Alternative) **NIC firmware + RDMA stack + GPU driver** for GPUDirect RDMA (`nvidia-peermem` or
  DMA-BUF): the data path needs all three plus kernel support.

**Common wrong answers.** Arguing only "fewer rows" without the missing-higher-order point; naming a
two-component coupling (driver + CUDA user-mode) as the three-way example.

Source: Section 16.7, Table 16.5 and Listing 16.10.
