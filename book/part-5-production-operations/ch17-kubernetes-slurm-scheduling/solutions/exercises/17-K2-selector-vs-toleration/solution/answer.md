# 17-K2 — nodeSelector versus toleration

**Attract vs repel.** A `nodeSelector` (or node affinity) *attracts*: the pod may run only on nodes
whose labels match; a taint *repels*: the node refuses pods that lack a matching toleration, and a
toleration only *permits* the pod onto the tainted node, it never sends it there.

To run a pod **only** on the dedicated search node you need both halves:

```yaml
spec:
  nodeSelector:
    halcyon.ai/dedicated: search
  tolerations:
  - key: halcyon.ai/dedicated
    operator: Equal
    value: search
    effect: NoSchedule
```

- Without the toleration the pod is repelled by orion-n31 and matches no other node → Pending
  (`untolerated taint`).
- Without the selector the pod is *allowed* onto orion-n31 but may land on any untainted node
  (lab note: J12 lands on n31 only because it carries the selector).

**Common mistakes:** toleration alone (half credit); `operator: Exists` without a key (tolerates
every taint); wrong effect (`NoExecute` does not match a `NoSchedule` taint).
Source: Section 17.2.3; lab cluster snapshot orion-n31.
