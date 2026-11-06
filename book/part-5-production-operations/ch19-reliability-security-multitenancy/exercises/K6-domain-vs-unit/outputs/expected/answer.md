# K6 — Domain vs unit: worked solution

**Relies on:** Section 19.6, step 3 ("Choose the smallest defensible failure domain"); Table 19.1; Table 19.6.

## Definitions applied to a failed `mlx5_3` link

- **Fault domain** = the set of components that actually failed or are suspected, as narrowed by the
  evidence. Here it is the rail-3 link of one node: the `mlx5_3` HCA port, its host-side optic, the
  cable/fiber, and possibly the switch-side optic. Direction-specific counters and DOM at both ends narrow
  it further (for example, switch-side receive errors with low host TX power point at the host
  transmitter path).
- **Scheduling unit removed** = the smallest thing the scheduler can take out of service so that no job
  uses the fault. For a TP = 8, rail-optimized training job that is the **whole node**. Each of the node's
  eight GPUs talks to its peers on its own rail, so a node with seven working rails cannot hold its place
  in the job. Every rail-3 collective would stall on the missing link. Slurm and Kubernetes schedule
  nodes or whole GPUs; they have no way to say "this node minus rail 3" for such a job.

So the fault domain is one link, but eight GPUs leave service. The repair ticket targets the link; the
drain targets the node.

## When the two coincide

- **The fault domain is itself the node**: a PSU, motherboard, or host-memory fault. Then the fault
  domain and the scheduling unit are both "the node". This is the clean coinciding case.
- **The unit shrinks toward the domain** when the workload is not rail-coupled across the whole node.
  A non-rail-aligned workload, such as a 4-GPU inference replica on GPUs 4–7 (rails 4–7), can keep using
  the node. If the scheduler allocates per GPU with NIC affinity, the unit removed shrinks to GPU 3 and
  its rail (one socket-side slice), which nearly matches the one-link fault domain. It is still slightly
  larger: GPU 3 itself is healthy but unusable without its NIC.

## Common wrong answers

- Quarantining the leaf (or the whole rail): this is a blast-radius error that removes 31 healthy nodes'
  rail.
- Saying "the domain is the node" because the node is drained: this confuses the two concepts the
  question asks you to separate.
- Removing only the GPU on rail 3 for a TP = 8 job: the job cannot use a seven-GPU node.
