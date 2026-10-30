# Chapter 17 — Exercises

Difficulty: ★ foundational · ★★ intermediate · ★★★ advanced. Tier: **L1** laptop/simulation,
**L2** single GPU host, **L3** multi-node GPU + RDMA. Every exercise states the evidence required
for grading. All cluster values refer to ORION (docs/REFERENCE_CLUSTER.md) and the lab snapshot
(`lab/data/`, seed 17) unless stated otherwise.

> **Safety:** exercises that change node, quota, or taint state (L2/L3) must run on a dedicated lab
> cluster you control — never on shared or production clusters.

---

## Knowledge checks

**17-K1** ★ L1 — A Kubernetes node reports `capacity nvidia.com/gpu: 8` and
`allocatable nvidia.com/gpu: 7`. `nvidia-smi -L` lists 8 GPUs. Explain the most likely mechanism
and what an 8-GPU pod will experience.
*Evidence required:* the component that sets the number, the mechanism, and the scheduler outcome.

**17-K2** ★ L1 — State the difference between a `nodeSelector` and a toleration, and write the
minimal pod-spec fragment that runs a pod *only* on a node labelled and tainted
`halcyon.ai/dedicated=search:NoSchedule`.
*Evidence required:* one sentence on attract vs repel; a correct YAML fragment.

**17-K3** ★ L1 — Name the three taint effects and say which of them can block scheduling and which
can evict running pods.
*Evidence required:* three effects with correct semantics.

**17-K4** ★★ L1 — A node has all eight H100s in MIG `all-1g.10gb` with the `mixed` strategy. What
resources does it advertise, and what happens to a pod requesting `nvidia.com/gpu: 1`? What changes
under the `single` strategy?
*Evidence required:* resource names and counts; the outcome under both strategies.

**17-K5** ★ L1 — Map each Slurm `squeue` reason to its meaning: `Resources`, `Priority`,
`QOSGrpGRES`, `ReqNodeNotAvail`.
*Evidence required:* four correct one-line meanings.

**17-K6** ★★ L1 — Why does the Kubernetes Topology Manager's `single-numa-node` policy not prevent
the scheduler from binding a pod to a node where alignment is impossible, and what failure pattern
results?
*Evidence required:* where the decision is made (scheduler vs kubelet) and the resulting loop.

**17-K7** ★★ L1 — In Slurm's classic fair-share formula `F = 2^(−U/S)`, compute `F` for an account
with usage equal to its share, half its share, and twice its share.
*Evidence required:* three values with arithmetic.

---

## Worked problems

**17-W1** ★★ L1 — Gang feasibility and cost. A 12-node partition (HX8 nodes) has free GPUs per node
`[8, 8, 0, 4, 6, 2, 8, 3, 5, 8, 1, 7]` for nodes p01–p12. Node p07 is `draining`; all nodes have all
rails up.
1. What does a naive "free GPUs" panel show, and how many free GPUs are eligible?
2. What is the largest multi-node gang (whole nodes) that can start now?
3. A 4-node gang is submitted. What pending reason does the Chapter 17 policy give, and why?
4. Under best-fit, where does a 6-GPU single-node job go?
5. Without gang scheduling, two 3-node jobs arrive when exactly four whole nodes are free and are
   scheduled pod by pod, interleaved. How many GPUs are stranded, and what does it cost if it lasts
   5 h at an `[ILLUSTRATIVE]` $2.50/GPU-hour?
6. A 128-GPU training job checkpoints every 45 min and takes 15 min (900 s) to restart. What does one
   preemption cost in GPU-hours on average?
*Evidence required:* every step as formula → substitution → result with units.

**17-W2** ★★★ L1 — Priority versus fair share on the Monday queue. In the lab snapshot, J01
(pretrain, 32 GPUs) is pending with `InsufficientCapacity` (manuscript Table 17.7). The pretraining
lead proposes raising J01 to priority 100.
1. Predict, by hand, the new placement for J01, J05, and J08 and the reason for each that does not
   start. (Hint: J01 and J05 are both pretrain at priority 100; which tie-breaker decides?)
2. Compare total GPUs placed and per-tenant GPUs placed with the baseline.
3. Identify the unintended consequence and propose a better policy (for example, a gang reservation
   or a separate QOS for urgent evaluations). Justify it with numbers from the snapshot.
4. Verify your prediction by editing a *copy* of `job_queue.json` and running your simulator.
*Evidence required:* the predicted table, the simulator output, the comparison, and the policy.

---

## Hands-on lab

**17-L1** ★★ L1 (L2/L3 extensions) — Complete [Lab 17](lab/README.md): implement
`starter/orion_sched.py` Tasks 1–6 and write `placement-report.md` and `pending-guide.md`.
*Evidence required:* `python check.py` output showing `9/9 checks passed`; the two reports per the lab
rubric. For an L2/L3 extension, the filled-in copy of `manifest.yaml` and the captured events or
`all_reduce_perf` results (≥ 5 repetitions, median and p95).

---

## Troubleshooting case

**17-T1** ★★★ L1 — "The inference pool has 21 free GPUs and my 8-GPU replica is pending." Evidence
`[ILLUSTRATIVE]` from the inference pool the morning after a driver canary on `orion-n30`:

```text
$ kubectl get pod chat-70b-replica-12 -n inference -o wide
NAME                  READY   STATUS    RESTARTS   AGE   IP       NODE     NOMINATED NODE
chat-70b-replica-12   0/1     Pending   0          47m   <none>   <none>   <none>

$ kubectl describe pod chat-70b-replica-12 -n inference | tail -3
  Warning  FailedScheduling  2m (x15 over 47m)  default-scheduler  0/8 nodes are available:
  1 node(s) had untolerated taint {halcyon.ai/dedicated: search}, 7 Insufficient nvidia.com/gpu.
  preemption: 0/8 nodes are available: 1 Preemption is not helpful for scheduling, 7 No preemption victims found for incoming pod.

$ kubectl get nodes -l halcyon.ai/pool=infer -o custom-columns='NAME:.metadata.name,GPU:.status.allocatable.nvidia\.com/gpu,MIG1G:.status.allocatable.nvidia\.com/mig-1g\.10gb'
NAME        GPU   MIG1G
orion-n25   8     <none>
orion-n26   8     <none>
orion-n27   8     <none>
orion-n28   0     56
orion-n29   8     <none>
orion-n30   0     <none>
orion-n31   8     <none>
orion-n32   8     <none>

$ kubectl get pods -n gpu-operator -o wide | grep orion-n30
nvidia-device-plugin-daemonset-q8w2d   0/1   CrashLoopBackOff   14   47m   ...   orion-n30
nvidia-driver-daemonset-m4k9z          1/1   Running            0    49m   ...   orion-n30

$ kubectl get resourcequota gpu-quota -n inference
NAME        AGE   REQUEST                           LIMIT
gpu-quota   90d   requests.nvidia.com/gpu: 27/48
```
GPU usage: n25 8, n26 4, n27 3, n29 4, n32 8 allocated; n28, n30, n31 have no GPU pods.

1. Reconcile the dashboard's 21 with the evidence: which free GPUs are ineligible and why?
2. Rank at least four hypotheses and give the discriminating command for each.
3. Identify the root cause that is *actionable* and the causes that are *by design*.
4. Propose a safe fix and a validation step. What must you *not* do?
*Evidence required:* the GPU reconciliation arithmetic, ranked hypothesis table, root cause, safe fix,
validation, and one prohibited action with the reason.

---

## Design challenge

**17-D1** ★★★ L1 — ORION-XL placement. ORION-XL has 512 HX8 nodes; each block of 32 nodes shares one
set of 8 rail leaves, and cross-block traffic crosses a spine tier with 2:1 oversubscription
`[ILLUSTRATIVE]` for this exercise. W-TRAIN is scaled to 64 nodes (512 GPUs). Design the placement
rules: (a) write the `topology.conf` structure (or the equivalent Kubernetes topology labels);
(b) decide whether a 64-node job must be confined to 2 blocks, may use 3, or may spread freely, and
quantify the cross-block traffic exposure; (c) choose a `--switches` (or equivalent) maximum wait and
defend it against the GPU-hours lost while waiting.
*Evidence required:* the config fragment, a modeled comparison of placements (show formula), and a
wait-time trade-off with numbers.

---

## Outline-mandated exercises

**17-M1** ★★ L1 — *Compare Kubernetes and Slurm for interactive inference, batch training, and
tightly coupled multi-node jobs.* Produce a table with at least eight criteria (unit of work,
gang support, topology awareness, rollout/upgrade model, autoscaling, quota/fair share, accounting,
health integration, user interface) and a recommendation for each workload class on ORION, plus the
operating rule that makes a hybrid safe.
*Evidence required:* the table, three recommendations each with one decisive reason, and the hybrid
rule.

**17-M2** ★★★ L1 — *Design a scheduling policy that considers GPU type, topology, quotas, queue
fairness, and gang placement* for ORION's training and inference pools. Specify: eligibility filters
and their order; GPU-type selection (labels/features); intra-node and multi-node topology rules;
quota model (hard, borrowing, overcommit ratio); priority classes and preemption asymmetry; fairness
key; gang mechanism; how small jobs are kept from fragmenting gang capacity; and the metrics that
prove the policy works. Validate one rule change by replaying the lab queue in your simulator.
*Evidence required:* a policy document (≤ 2 pages) and before/after simulator output for one rule.

**17-M3** ★★ L1 (L2 optional) — *Troubleshoot a job that is pending despite apparently free GPUs;
list scheduler, device-plugin, topology, quota, and node-health evidence.* Write a troubleshooting
guide organised by evidence source, with the exact Kubernetes and Slurm commands, what each output
proves, and the decision order. Apply it to lab cases P03 and P11 and show your reasoning.
*Evidence required:* the guide with commands per evidence class; the two applied diagnoses with the
evidence lines quoted.

---

## Reflection and review

**17-R1** ★ L1 — The lab simulator attempts each job once in a single pass. Name two real scheduler
behaviours this hides and how each could change Table 17.7.
*Evidence required:* two behaviours and a concrete effect on at least one job.

**17-R2** ★★ L1 — Fair share in the lab uses instantaneous `used/quota`. What would change with
Slurm's decayed usage (`PriorityDecayHalfLife=7-0`), and which tenant on Monday morning would most
likely benefit?
*Evidence required:* the mechanism and a reasoned answer.

**17-R3** ★★ L1 — The rack-compact rule assumes rack events are independent. Give one reason this is
false on ORION and how it changes the rule.
*Evidence required:* a correlated failure mode and a modified rule.

**17-R4** ★ L1 — What evidence would you still need before claiming that confining small jobs to
"shared" nodes reduced gang queue wait in production?
*Evidence required:* the measurement plan (metric, window, comparison, confounders).

---

## Chapter deliverable

**17-DEL** — *Workload placement policy and scheduling troubleshooting guide.* Submit the policy from
17-M2 and the guide from 17-M3 as one document, with the lab's `placement-report.md` as an appendix.
*Evidence required:* the document, the lab checker output (`9/9`), and the replay evidence from 17-M2.
