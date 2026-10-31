# 17-M1 — Kubernetes versus Slurm by workload class

| Criterion | Kubernetes (default + add-ons) | Slurm |
|---|---|---|
| Unit of work | Pod / Deployment: long-lived replicas reconciled to desired state | Job / step with a finite run time |
| Gang support | Needs Kueue/Volcano admission; pods otherwise bind one by one | Atomic allocation by construction |
| Topology awareness | Topology Manager (node-local, after binding), Kueue TAS, labels, DRA | `gres.conf` cores, `topology.conf` tree/block, `--switches` |
| Rollout / upgrade model | Rolling updates, PodDisruptionBudgets, probes | Drain and requeue; no service abstraction |
| Autoscaling | HPA/KEDA on serving metrics, cluster autoscaler | Static partitions; power saving |
| Quota / fair share | ResourceQuota (hard), Kueue ClusterQueue with cohorts and borrowing | QOS limits, associations, multifactor/Fair Tree with decayed usage |
| Accounting | External (metrics pipeline, Kueue usage) | `slurmdbd`, `sacct`/`sreport` built in |
| Health integration | Device-plugin health, node conditions, probes, NoExecute taints | NHC drain, node reasons, requeue |
| User interface | YAML + containers, `kubectl` | `sbatch`/`srun`/`squeue`, scripts |
| Launcher for coupled ranks | Training operator (PyTorchJob/MPIJob) | `srun` lock-step launch |

**Recommendations for ORION:**
- **Interactive inference (W-INFER) → Kubernetes.** Decisive reason: the service abstraction with
  rolling updates, health probes, and autoscaling on TTFT/queue depth; Slurm has no rolling update.
- **Single-node batch → either.** Decisive reason: neither default is weak; colocate with whichever
  pool it shares capacity with (Slurm in the training pool for queue/fair-share/accounting, or
  Kubernetes + Kueue if the platform is Kubernetes-first).
- **Tightly coupled multi-node (W-TRAIN) → Slurm.** Decisive reason: atomic gang allocation with
  `srun` launch, topology (`--switches`), and checkpoint requeue out of the box; Kubernetes only with
  gang admission + topology labels + a training operator, and with gang time-to-start measured as
  an SLI.

**Hybrid rule.** The fleet lifecycle system (Chapter 16) owns node state and both schedulers
derive from it; a node belongs to exactly one scheduler at a time; moving a node between pools is a
lifecycle transition (`schedulable` in Slurm → `draining` → `drained` → relabel and rejoin →
`validated` → `schedulable` in Kubernetes), never a hot handover.

Source: Section 17.7, Table 17.5; Section 17.5.5.
