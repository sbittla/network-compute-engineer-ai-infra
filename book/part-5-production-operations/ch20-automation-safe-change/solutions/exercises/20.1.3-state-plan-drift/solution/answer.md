# 20.1.3 — IaC state, plan and drift: worked answer

**Relies on:** manuscript Section 20.4 and Table 20.5 (Terraform/OpenTofu vocabulary,
`[VENDOR-SPEC, 2026-10]`).

## Model answer

- **State** is the tool's record of which real objects it manages and their last-known attributes. It is
  not the real infrastructure; it is a cache of what the tool believes. Lost or corrupted state can make
  the tool try to create duplicates or destroy live objects, so it lives in a locked, encrypted, backed-up
  remote backend.
- **Plan** is the computed diff between the configuration (desired) and the real or recorded state,
  expressed as create, update in place, replace (destroy-then-create), or destroy actions. The plan is the
  reviewable artifact.
- **Drift** is real state that differs from the recorded or declared state, typically from hand edits
  (for example a leaf QoS map changed during an incident). A refresh detects it; policy decides whether
  the tool reverts it or a human reconciles first.

**The action that should stop a fabric reviewer:** any **destroy** or **replace** of a fabric object
(a VLAN, a VRF, a BGP neighbour, a leaf port profile). Some attribute changes force destroy-and-recreate,
and on a network object that is an outage for every tenant using it, not a "modification". In CI, a plan
containing a destroy or replace of a protected resource class should fail unless an explicit, reviewed
override is present.

A related habit: **apply the saved, reviewed plan file**. Running `apply` without one computes a fresh plan
that may differ from the one the reviewer read.

## Marking notes (4 points)

1 point each for state, plan and drift; 1 point for naming destroy or replace with the outage reasoning.

**Common wrong answers.** Treating state as "the real config". Assuming `apply` re-uses the reviewed plan
(it does not unless given the saved plan). Naming "update in place" as the alarming action: updates can be
risky, but replace and destroy are the actions that remove an object.
