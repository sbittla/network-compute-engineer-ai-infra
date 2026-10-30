# Chapter 7 — Ethernet and Data-Center Network Foundations

**Part III — Networking for AI Clusters · Course week 4 · Progressive Lab 2 (Fabric design)**

AI training traffic is a few huge, synchronized, low-entropy flows, and the slowest one gates every
GPU. This chapter builds the routed fabric foundations that the rest of Part III depends on: Layer 2
vs Layer 3 at the host, /31 and IPv6 addressing, MTU and path-MTU blackholes, RFC 7938 eBGP and ASN
design, ECMP hashing and its failure modes for RDMA, leaf-spine and rail-optimized Clos arithmetic,
QoS basics, BFD and convergence, and precisely what a link, spine, or leaf failure does to capacity.
Everything is worked on the ORION-256 backend. In the lab you build a tool that sizes, addresses, and
validates that fabric and catches the configuration errors that cause real outages.

## Learning objectives

1. **Explain** why AI back-end fabrics are routed to the host (L3 leaf-spine) rather than built as
   large Layer 2 domains, and what each design gives up.
2. **Design** an IPv4/IPv6 point-to-point addressing plan with /31 (or /127) links, loopbacks, and
   summarizable per-rail aggregates, and an RFC 7938 eBGP ASN plan.
3. **Calculate** leaf and spine counts, oversubscription, cabling, the maximum size of a two-tier Clos,
   and the frame sizes that a given IP MTU and RoCEv2 path MTU produce.
4. **Analyze** ECMP behaviour for low-entropy AI flows: 5-tuple hashing, collision probability, hash
   polarization, and resilient hashing.
5. **Predict** the capacity and convergence consequences of a link, spine, or leaf failure in a
   rail-optimized fabric, distinguishing raw uplink capacity from ECMP-aware capacity.
6. **Diagnose** MTU mismatches (including PMTUD blackholes), asymmetric routing, and incorrect route
   advertisements using a structured evidence checklist.
7. **Validate** a fabric intent dataset automatically, catching duplicate /31s, ASN collisions, MTU
   mismatches, missing ECMP `maximum-paths`, and asymmetric or bogus advertisements.

## Prerequisites

- IP networking literacy: subnets, routing tables, TCP/UDP.
- [Chapter 2](../../part-1-foundations/ch02-anatomy-of-an-ai-data-center/) (ORION and its three
  networks), [Chapter 3](../../part-1-foundations/ch03-linux-host-systems-diagnostics/) (Linux
  networking tools), [Chapter 5](../../part-2-accelerated-compute/ch05-gpu-interconnects-host-topology/)
  (GPU-to-NIC locality and rails).
- Python 3.10+ for the lab.

## Estimated time

| Activity | Time |
|---|---|
| Reading (manuscript) | 2.5–3 h |
| Exercises | 3–4 h |
| Lab (L1) including design note | 4–5 h |
| L2 extension (containerlab + FRR) | +3 h (optional) |

## Lab tier(s)

**L1** (laptop, standard-library Python, < 1 s). Optional **L2** (container fabric with FRRouting) and
**L3** (dedicated physical leaf-spine lab with RoCEv2 hosts) extensions.

## Deliverable (from the course outline)

**Topology diagram, routing policy summary, and failure-convergence analysis** — produced as the lab's
design note (lab Task 6) and exercise 7.O2.

## File map

| Path | Contents |
|---|---|
| [manuscript.md](manuscript.md) | Chapter text (Sections 7.1–7.12, trade-offs, runbook, further reading) |
| [exercises.md](exercises.md) | Knowledge checks, worked problems, lab, troubleshooting case, design challenge, reflection, outline-mandated exercises |
| [lab/README.md](lab/README.md) | Lab guide: tasks, conventions, rubric, L2/L3 extensions |
| `lab/manifest.yaml` | Environment manifest (tier, seed, extension recording fields) |
| `lab/data/` | Synthetic ORION-256 fabric intent (devices, links, advertisements) with planted errors |
| `lab/tools/` | Dataset generator — instructor copy only (not in the student release) |
| `lab/starter/fabric_lab.py` | Learner module with TODOs |
| `lab/check.py` | Automated checker (19 checks) |
| `solutions/` | Instructor-only: exercise key and reference implementation |
| `review/REVIEW.md` | Editorial review log |

## Course placement

Week 4 — *Ethernet, L2/L3 and BGP fabrics*: VLANs, IP, MTU, BGP, ECMP, leaf-spine, QoS and
convergence. Deliverable: fabric design and failure analysis. Followed by
[Chapter 8](../ch08-rdma-rocev2-infiniband/) (week 5).
