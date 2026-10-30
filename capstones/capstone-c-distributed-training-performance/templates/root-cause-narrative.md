# Root-Cause Narrative

Follow the diagnostic loop. One paragraph per stage, with evidence references and labels.

## 1. Symptom

<fill: what was observed, by whom, at which scale; the number that made it a problem>

## 2. Evidence collected

| Evidence | Source | What it shows |
|---|---|---|
| <fill> | | |

## 3. Hypotheses (ranked before testing)

| # | Hypothesis | Prediction if true | Discriminating test | Result |
|---|---|---|---|---|
| H1 | <fill: e.g., inter-node collectives on a slow transport> | <fill: intra-node busbw normal, inter-node busbw ≪ 350 GB/s, NCCL log shows Socket> | <fill> | <fill> |
| H2 | <fill: e.g., straggler node> | <fill> | <fill> | <fill> |
| H3 | <fill: e.g., gradient-bucket overlap> | <fill> | <fill> | <fill> |

## 4. Root cause

<fill: mechanism, in one paragraph: what moved where, how many bytes, at what bandwidth, why it was
exposed. Separate what is proven from what is correlated.>

## 5. Change and validation

<fill: the single change, how it was rolled out, the before/after table with CIs, and the check that
prevents regression.>

## 6. What did not help, and why we say so

<fill: the bucket-size change; the honest statement of a non-significant result.>
