# 17-T1 · 21 free GPUs and a pending 8-GPU replica (★★★ · L1)

Type: troubleshooting · Kind: computed · Points: 10

<!-- prompt:start -->
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
<!-- prompt:end -->

## Before you start

- **Chapter:** Chapter 17 of the book; every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) and the lab snapshot in [lab/data/](../../lab/data/) (seed 17).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Write your diagnosis in `outputs/answer.md`, one section per numbered part. For part 1, show the GPU
reconciliation as a per-node count that adds up to 21 and marks each ineligible GPU with its reason. For
part 2, use a table (hypothesis, rank, discriminating command, what each result would mean). Quote the
evidence lines above that support your root cause, and label any number you use.
