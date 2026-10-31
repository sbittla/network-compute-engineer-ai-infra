# 17-K6 — Topology Manager rejection loop

**Where the decision is made.** The kube-scheduler filters and binds on node-level resource
*counts* (`allocatable` minus requested); it does not evaluate NUMA alignment. The kubelet's
Topology Manager evaluates NUMA hints from the CPU, Memory, and Device managers at **pod admission
on the node, after binding**.

**Failure pattern.** Under `single-numa-node` (or `restricted`), a pod that cannot be aligned, e.g.
a 4-GPU pod on an HX8 whose free GPUs are 2 on socket 0 and 2 on socket 1, is rejected by the
kubelet: the pod ends in phase `Failed` with reason `TopologyAffinityError`; it is not retried in
place. If a controller (Deployment, Job) owns it, the controller creates a replacement, the
scheduler still sees 4 free GPUs on that node and can bind it there again → **reject / recreate
loop**, visible as a growing count of failed pods and no running replica.

**Mitigations (any one):**
- replica sizes that always fit one socket on an HX8 (1, 2, or 4 GPUs) with socket best-fit
  packing, never 3 + 3 + 2;
- scheduler-visible topology: DRA device attributes, or node labels consumed by affinity;
- `best-effort` policy during migration (the only policy that admits misaligned pods;
  `restricted` rejects too).

**Common mistake:** claiming `restricted` avoids rejection. Source: Section 17.2.4, Table 17.1.
