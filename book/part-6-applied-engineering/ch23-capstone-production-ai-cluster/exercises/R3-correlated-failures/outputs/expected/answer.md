# R3 — Correlated failures and the optimal checkpoint interval (model answer)

**Source:** manuscript Section 23.5 ("The goodput cost of failures", "Correlated failures"), Section 23.10 Step 7; key R3.

**Model answer (≈ 130 words).** Young's τ ≈ sqrt(2·δ·M) assumes independent failures at a constant rate.
On ORION a realistic correlated mechanism is a bad NIC firmware rollout: once deployed to all 32 nodes,
link resets hit many nodes within hours, so job interruptions arrive in a burst rather than once per
48 h. Others are a cooling-loop event affecting every rack on the loop, or infant mortality in a new
node batch. The effect is that M is not one number: the long-run average may still be ≈ 48 h, but during
a burst the effective M is a few hours. A fixed τ = 4,554 s (≈ 76 min) tuned to 48 h is then too long:
with M = 4 h, sqrt(2 × 60 × 14,400) ≈ 1,315 s is optimal. Remedies: adaptive intervals driven by recent
incident rate, burst-triggered checkpoints after a first failure, and staged firmware rollouts that
prevent the correlation.

**Deduct for** mechanisms without an ORION component or no stated effect on τ.
