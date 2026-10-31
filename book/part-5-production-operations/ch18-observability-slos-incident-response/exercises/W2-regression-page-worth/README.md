# W2 · Is a 9 % regression worth a page? (★★★ · L1)

Type: worked-problem · Kind: computed · Points: 10

<!-- prompt:start -->
**W2 ★★★ L1 — Is a 9 % regression worth a page?** A 4,096-GPU ORION-XL job's step time rises from
17.4 s to 19.0 s because of a fabric problem.
(a) Compute the throughput ratio and the fraction of GPU time lost.
(b) Case A: nobody notices for 6 h; mitigation takes another 30 min. Case B: an alert detects it in
12 min; mitigation takes 30 min. Compute lost GPU-hours and cost at $3 per GPU-hour for each.
(c) Would ORION's `TrainingThroughputFastBurn` rule (threshold 1.10 × baseline) fire? If not, propose
a threshold for jobs above 1,024 GPUs and state the evidence you would need that it will not be noisy.
*Evidence required:* arithmetic for (a)–(b); a justified threshold for (c) with a noise argument.
<!-- prompt:end -->

## What to submit

Write your working in `outputs/answer.md`: formula → substitution → result with units for every
part, with evidence labels. If you check it with a script, save it as `outputs/work.py` and run it
from this folder with `python outputs/work.py`.
