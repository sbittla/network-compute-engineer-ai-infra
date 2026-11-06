# 7.D — Parallel links and spine count for the next build (★★★, L1)

Type: Design challenge · kind: `computed` · 15 points

## Prompt

<!-- prompt:start -->
**7.D** ★★★ L1 — **Parallel links and spine count for ORION-256's next build.** Compare:

- **A.** 4 spines × 8 parallel links per leaf, one eBGP session per link (the current design).
- **B.** 8 spines × 4 parallel links per leaf, one eBGP session per link.
- **C.** 4 spines, one 8-member LAG per leaf-spine pair, one eBGP session per LAG, micro-BFD (RFC 7130).

For each option quantify: ECMP-aware ingress capacity after one link failure and after one spine
failure; spine-layer bisection after one spine failure; eBGP and BFD session counts; spine switches
and spine ports used; and ECMP width at the leaf. Then recommend one option for a fabric whose
largest risk is optics failures (several link failures per month) and justify it in ≤ 300 words.
*Evidence required:* a comparison table with arithmetic, a recommendation, and one stated assumption
that would change your recommendation.
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md) for the ORION-256 backend, and the Section 7.3 conventions (Table 7.2).
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare your method with the worked solution and marking scheme in the chapter's `solutions/exercises/7.D-parallel-links-spines/` (instructor material in the full repository; removed from student releases).

## What to submit

Quantify every metric for A, B and C with arithmetic, then recommend in ≤ 300 words. Put every deliverable in `outputs/`:

- `outputs/answer.md`
