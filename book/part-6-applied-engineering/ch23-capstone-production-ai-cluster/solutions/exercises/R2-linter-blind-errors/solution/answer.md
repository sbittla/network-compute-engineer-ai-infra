# R2 — A class of design error the linter cannot catch (model answer)

**Source:** manuscript Section 23.4 (invariants are consistency checks), Section 23.6 (roles,
Table 23.7 checklist), Section 23.11; key R2.

**Model answer (≈ 130 words).** The linter checks *consistency*: numbers in one document agree with
numbers in another, labels exist, references resolve. It cannot catch a design that is consistent but
wrong. Example: a bundle with TP = 16 across two HX8 nodes, PP = 2, DP = 8 passes every invariant
(16 × 2 × 8 = 256, ports and power fine), yet puts per-layer tensor-parallel all-reduces on 50 GB/s NICs
instead of 450 GB/s NVLink, a 9× slower path that would dominate step time. Other members of the class: a
lossless configuration likely to cause pause storms, or a workload model with the wrong tokens per step.
A design review catches it because a compute or network reviewer, working through the Table 23.7
checklist, re-derives the communication model and asks "what would make this fail?"; the linter only
asks "do these files agree?".

**Deduct for** naming an error the linter does catch (unlabelled numbers, port overflow).
