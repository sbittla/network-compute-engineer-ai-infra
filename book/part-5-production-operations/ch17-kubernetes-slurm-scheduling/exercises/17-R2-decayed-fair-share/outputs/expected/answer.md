# 17-R2 — Decayed usage versus instantaneous share

**Mechanism.** With `PriorityDecayHalfLife=7-0`, Slurm accumulates each account's usage (GPU-seconds
via TRES billing) and multiplies past usage by 0.5 every 7 days, so usage from a week ago counts half,
two weeks ago a quarter. The fair-share factor (`2^(−U/S)` classic, or Fair Tree rank) is computed
from that *decayed history*, not from what is running at the instant. Consequences: a tenant that just
finished a large run keeps a low factor even with nothing running; a tenant idle all week gets a
high factor even if it starts something now.

**Monday morning on ORION.** pretrain has had 96 GPUs (R-pt-001 + R-pt-002, 12 nodes) running for days
→ highest decayed usage relative to its share → it would rank *even lower* than in the lab's
instantaneous 0.600–0.700. research (18 GPUs) and finetune (10 GPUs), typically bursty and lightly
loaded over the weekend, would benefit most; research is the most likely winner because its recent
usage is lowest relative to its 48-GPU share, and it already won J08 under the instantaneous model.
Inference serving is usually in its own pool/QOS and should not compete through fair share at all.

**Design note.** Decay prevents a tenant from "banking" idle time indefinitely and smooths
oscillation, but makes the factor harder to explain from a snapshot; publish `sshare` output so
tenants can see why. Accept any answer that reasons from decayed usage. Source: Sections 17.4.4,
17.5.4.
