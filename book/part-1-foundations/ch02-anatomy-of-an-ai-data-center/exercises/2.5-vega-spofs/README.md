# Exercise 2.5 — Five single points of failure

**Difficulty:** ★★ · **Tier:** L1 · **Type:** outline-mandated · **Kind:** written · **Points:** 15

## Prompt

<!-- prompt:start -->
*(Outline-mandated: identify at least five single points of failure in a sample cluster design and
propose mitigations.)*

**VEGA** is a 64-GPU inference cluster (8 HX8 nodes) a contractor proposed for Halcyon. Design notes
`[ILLUSTRATIVE]`:

- Two GPU racks of 4 nodes, each with A and B rack PDUs from separate UPS systems. One network rack
  with a single rack PDU on feed A.
- One sidecar liquid-to-air CDU per GPU rack.
- Frontend: each node dual-homed to two leaves (MLAG pair) in the network rack; one border router; a
  single hardware load balancer in front of the inference service.
- Model weights served from one NFS server; nodes fetch weights at pod start.
- Kubernetes control plane: three VMs on one hypervisor host in the network rack.
- DNS and NTP: one VM on the same hypervisor host.
- OOB: one 1 GbE switch for all BMCs and PDUs.

Tasks: (1) identify at least five SPOFs, stating the service impact of each; (2) draw the
failure-domain diagram; (3) propose a mitigation for each and decide fix or accept, with a reason
that refers to cost, likelihood, or recovery time; (4) identify one dependency that is a SPOF only
because of *where* something is placed or plugged, not because of how many there are.

**Evidence required:** SPOF table (component, impact, mitigation, fix/accept, reason); failure-domain
diagram; answer to task 4.
<!-- prompt:end -->

## What to submit

Put every deliverable in [`outputs/`](outputs/):

- `outputs/spofs.md`: SPOF table (component, impact, mitigation, fix/accept, reason) and the task 4 answer
- `outputs/failure_domains.md`: failure-domain diagram (Mermaid or image)

Label every number you produce (`[MODELED]`, `[ILLUSTRATIVE]`, `[MEASURED]` and so on) and show formula, substitution and result with units.
