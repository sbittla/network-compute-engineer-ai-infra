# W2 — Checkpoint interval and goodput (M = 24 h variation)

**Source:** manuscript Section 23.5 ("The goodput cost of failures") and Section 23.10 Step 7; key W2.
Values `[MODELED]` from the stated `[ILLUSTRATIVE]` inputs. Model: τ ≈ sqrt(2·δ·M) (Young 1974);
waste ≈ δ/τ + (τ/2 + R)/M.

Inputs: δ = 60 s, R = 900 s, M = 24 h = **86,400 s** (pessimistic variation: node MTBF 768 h / 32 nodes;
canonical is 1,536 / 32 = 48 h).

## 1. Interval and waste terms

- τ = sqrt(2 × 60 × 86,400) = sqrt(10,368,000 s²) = **3,219.9 s ≈ 53.7 min**.
- δ/τ = 60 / 3,219.9 = **1.863 %**.
- τ/(2M) = 3,219.9 / 172,800 = **1.863 %** (equal to δ/τ at the optimum: a built-in arithmetic check).
- R/M = 900 / 86,400 = **1.042 %**.
- Total failure-related waste = 1.863 + 1.863 + 1.042 = **4.77 %**.

## 2. Lost GPU-hours per failure

Lost time per failure = τ/2 + R = 1,610.0 + 900 = 2,510.0 s; × 256 GPUs / 3,600 s/h = **178.5 GPU-hours**.

## 3. Run duration

Goodput = 1 − 0.0477 − 0.05 = **0.9023**. Duration = 96.00 / 0.9023 = **106.39 days**.

## 4. First backlog item

**Reduce δ by validating asynchronous checkpointing.** With δ = 5 s: τ = sqrt(2 × 5 × 86,400) = 929.5 s;
δ/τ = τ/(2M) = 0.538 % each → 1.076 % + R/M 1.042 % = **2.12 %** total, saving ≈ 2.65 points of goodput:
96.00 / 0.9288 = 103.36 days, **≈ 3.0 days shorter**. Reducing R (faster requeue, pre-staged images) is a
strong second: R/M is a fixed 1.04 % here, half the remaining waste once δ is small. Spare nodes are only
an explicit variation (ORION has none). Doubling storage bandwidth is the weakest lever: it only shrinks
the 12.25 s write floor inside δ = 60 s. Canonical comparison (M = 48 h): 3.16 % waste (Section 23.10).

**Common wrong answers.** Mixing M in hours with δ in seconds (τ ≈ 54 s instead of 3,220 s); adding
waste fractions to goodput instead of subtracting; dividing 96 days by (1 − 0.05) only; recommending more
storage bandwidth without computing its effect.
