# 17-K3 — The three taint effects

| Effect | New pods without a toleration | Running pods without a toleration |
|---|---|---|
| `NoSchedule` | **Blocked** (not scheduled) | Stay |
| `PreferNoSchedule` | Scheduler *avoids* the node but may still use it; **never blocks** | Stay |
| `NoExecute` | **Blocked** | **Evicted**, immediately or after the toleration's `tolerationSeconds` |

**Blocking:** `NoSchedule` and `NoExecute`. **Evicting:** `NoExecute` only.

Operational consequences on ORION: the lab's `PreferNoSchedule` canary taint on orion-n30 is a red
herring and must not make the node ineligible (J13 lands there; pending case P09 is the control);
Chapter 16 maps `repair`/`retired` to a `NoExecute` taint so that nothing keeps running on a
faulty node, while a cordon (`spec.unschedulable`, which the node controller also expresses as
the `node.kubernetes.io/unschedulable:NoSchedule` taint) only stops new pods.

**Common mistakes:** treating `PreferNoSchedule` as blocking (lab check T1); believing
`NoSchedule` evicts running pods. Source: Section 17.2.3, Section 16.11 (Table 16.6).
