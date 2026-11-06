# 10.W2 — FEC arithmetic and sparing at ORION-XL scale (★★★, L1)

**Type:** Worked problem · **Kind:** computed · **Points:** 10

## Prompt

<!-- prompt:start -->
**10.W2 — FEC arithmetic and sparing at ORION-XL scale (★★★, L1).**
(a) An 800G port uses eight 100G lanes with the same 256b/257b + RS(544,514) overheads as 400G.
Compute the line rate and the codeword rate. (b) A port runs at pre-FEC BER 2 × 10⁻⁵. Compute its
margin in decades to 2.4 × 10⁻⁴ and estimate the fraction of codewords that contain at least one
symbol error (use the symbol error probability p ≈ 10 × BER and P(≥1) = 1 − e^(−544p)). (c) ORION-XL
has 16,384 backend optics with an AFR of 1.5 % and a 21-day resupply lead time. Using a Poisson model,
how many spares give ≥ 95 % and ≥ 99 % probability of not running out during one lead time?
(d) Explain why the rate-based policy (3 %) gives a much larger number, and when you would use each.
*Evidence required:* formulas and numbers for (a)–(c) (a table of cumulative Poisson probabilities is
acceptable); ≤ 120 words for (d).
<!-- prompt:end -->

## Before you start

- **Chapter:** [manuscript.md](../../manuscript.md); every exercise prompt is also in [exercises.md](../../exercises.md).
- **Defaults:** Unless the prompt says otherwise, use the ORION values in [docs/REFERENCE_CLUSTER.md](../../../../../docs/REFERENCE_CLUSTER.md). Values are `[ILLUSTRATIVE]` unless labelled otherwise.
- **Checking your work:** Check units and orders of magnitude against the chapter's worked examples. After you have your own answer, compare it with [outputs/expected/](outputs/expected/README.md): the reference script's output (`result.md`), the worked solution (`answer.md`) and the marking scheme (`marking.md`).

## What to submit

Put your deliverables in `outputs/` in this folder:

- `outputs/answer.md`: the worked answer: formula, substitution, result with units, decision sentence
- `outputs/work.py`: optional: a script that reproduces your numbers

Show every formula, substitution and result with units, and label each number with its evidence label.
