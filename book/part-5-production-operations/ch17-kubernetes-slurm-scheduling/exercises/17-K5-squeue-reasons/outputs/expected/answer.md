# 17-K5 — Slurm squeue pending reasons

| Reason (`squeue -o %R`) | Meaning | First evidence to check |
|---|---|---|
| `Resources` | The job is at the head of its partition's queue and the requested resources are not available *now* | `sinfo -N -O NodeList,StateLong,GresUsed`: is it capacity or shape (fragmentation)? |
| `Priority` | Higher-priority pending jobs are ahead of it; it will be considered after them | `sprio -j <id>` for the factor breakdown |
| `QOSGrpGRES` | The QOS group limit on a generic resource (here GPUs, `GrpTRES=gres/gpu=N`) is reached | `sacctmgr show qos`, `squeue -q <qos>` usage |
| `ReqNodeNotAvail` | Nodes the job requires (or all candidate nodes) are down, drained, or reserved | `sinfo -R`, `scontrol show node`, `scontrol show reservation` |

**Interpretation notes.** `Resources` is the reason a *fragmented* partition shows: the lab's P03
has 34 free GPUs but only one whole node for a 4-node gang. A job at the head of the queue with
`Resources` is also the job Slurm's backfill reserves nodes for. `QOSGrpGRES` is policy, not
capacity; never "fix" it by adding nodes. `ReqNodeNotAvail` often follows a lifecycle drain
(Chapter 16), and the reason string lists the unavailable nodes.

Source: Section 17.5.3.
