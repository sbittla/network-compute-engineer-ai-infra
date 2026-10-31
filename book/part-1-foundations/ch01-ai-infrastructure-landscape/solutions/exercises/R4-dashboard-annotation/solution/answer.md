# R4 — Dashboard annotation for the Section 1.11 incident

Source: manuscript Section 1.11 (utilization stayed at 96–97 % while step time doubled) and the Pitfall
in Section 1.6.

**Annotation to place on the "GPU utilization" panel:**

> GPU utilization = fraction of time *any* kernel was running, including NCCL kernels spinning while they
> wait for peers. It does **not** show compute efficiency. For that, use the *SM active* and *Tensor
> active* panels below (`DCGM_FI_PROF_SM_ACTIVE`, `DCGM_FI_PROF_PIPE_TENSOR_ACTIVE`) and the job's
> step-time panel. **If tensor activity drops while utilization stays flat, suspect communication or
> waiting** (placement, a straggler, the network), not the GPU. Incident 48377 (Section 1.11): utilization
> 96–97 % throughout while step time doubled.

Why this wording works: it defines the metric in one line, names the better panels by their field names
so the engineer can find them, gives one actionable rule, and links a real incident as the worked
example. A good answer also suggests moving the tensor-active panel next to utilization so that the
contrast is visible at a glance.
