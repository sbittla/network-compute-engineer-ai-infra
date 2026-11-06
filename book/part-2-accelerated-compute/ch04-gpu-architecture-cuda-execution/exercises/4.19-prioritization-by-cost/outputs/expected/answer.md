# 4.19 — Why "fix the most interesting finding first" is a bad rule (model answer)

Relies on manuscript Section 4.12 (Table 4.11) and the chapter's trade-offs section.

Interest correlates with novelty and technical depth, not with how much time a finding costs. In the
worked example the most interesting finding is the register-limited `layernorm_bwd_fused_kernel`
(12.5 % occupancy, 21.6 % of the HBM roof): it invites kernel work, launch-bound tuning and Nsight Compute
sessions, yet it saves only **2.43 ms** per step `[MODELED]`. The dull pageable H2D copy saves **8.77 ms**,
8.77 / 2.43 = **3.6×** more, and is a one-line fix (pinned staging plus a side-stream prefetch). The debug
`.item()` hook (5.30 ms) and the unfused optimizer (5.55 ms) are also larger and cheaper than the kernel
rewrite.

Better rule: rank by **modeled saving × confidence ÷ effort**, fix and validate one change at a time, and
re-measure before moving down the list, because savings interact.

(≈ 130 words.)
