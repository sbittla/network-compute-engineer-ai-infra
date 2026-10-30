# Chapter 7 — Exercises

Difficulty: ★ foundational · ★★ intermediate · ★★★ advanced. Tier: L1 laptop/model · L2 single host
or container lab · L3 dedicated multi-node hardware lab. Every exercise states the **evidence
required** for grading. Answers and marking guidance: `solutions/exercises-key.md` (instructors).

Unless an exercise says otherwise, use the ORION-256 backend from
[docs/REFERENCE_CLUSTER.md](../../../docs/REFERENCE_CLUSTER.md) and the conventions in
[manuscript.md](manuscript.md) Section 7.3 (Table 7.2). Exercises marked **[Outline]** are mandated by
the course outline.

> **Safety:** No exercise asks you to change a shared or production network. Failure and change
> exercises use models, containers, or a dedicated lab fabric.

---

## Knowledge checks

**7.K1** ★ L1 — State the RFC that permits /31 prefixes on point-to-point links and the IPv6
equivalent prefix length. How many IPv4 addresses do ORION's 512 point-to-point links consume with
/31s, and with /30s? Give one operational (not address-conservation) reason to prefer /31s.
*Evidence required:* RFC numbers, both address counts with arithmetic, one operational reason.

**7.K2** ★ L1 — In an RFC 7938 fabric, why do all spines share one ASN while every leaf has a unique
ASN? Describe precisely what goes wrong if two leaves are given the same ASN.
*Evidence required:* the loop-prevention mechanism in one sentence for each half of the question.

**7.K3** ★★ L1 — A leaf-spine link has MTU 9216 on one end and 1500 on the other. Explain why the
eBGP session on that link comes up and stays up, and which traffic fails.
*Evidence required:* the role of the TCP MSS; the direction(s) in which large frames are lost.

**7.K4** ★★ L1 — Compute the on-the-wire frame size (including FCS) of a RoCEv2 RDMA WRITE first
packet carrying a 4,096-byte payload over IPv4. What RDMA active MTU would a NIC select if its netdev
MTU were 1500, and why does ORION set the host MTU to 9000 when RoCE frames are only about 4.2 KB?
*Evidence required:* a header-by-header sum; the selected MTU with justification.

**7.K5** ★★ L1 — Define hash polarization. Using the leaf-uplink numbering in Section 7.6, show
which of a spine's 8 downstream links are used when leaf and spine use the same hash *h mod n*.
*Evidence required:* the modular-arithmetic argument and the resulting link set.

**7.K6** ★★ L1 — One of the 8 links between orion-be-leaf-r0 and orion-be-spine-1 fails. Why does the ECMP-aware
ingress capacity of orion-be-leaf-r0 fall by 12.5 % when its raw uplink capacity falls by only 3.1 %?
*Evidence required:* both numbers with arithmetic and the one-sentence mechanism.

**7.K7** ★ L1 — What is a gray failure? Which detection mechanism in Table 7.7 catches it, and
roughly how long does detection take with 300 ms × 3 BFD versus 3 s / 9 s BGP timers?
*Evidence required:* definition, mechanism, two detection times.

**7.K8** ★ L1 — Why is a single leaf a *cluster-wide* fault domain in ORION, whereas a top-of-rack
leaf failure in a conventional design affects one rack?
*Evidence required:* the rail mapping argument and its effect on a 256-GPU job.

---

## Worked problems

**7.W1** ★★ L1 **[Outline: design a two-tier leaf-spine for a specified number of GPU racks and
calculate uplink/downlink ratios]** — Halcyon plans **ORION-384**: 12 GPU racks × 4 HX8 nodes
(48 nodes, 384 GPUs, 8 × 400G backend NICs per node), 64 × 400G switches.

(a) Design a **rail-optimized, 1:1** two-tier backend. Give leaves per rail, total leaves, spines,
links per leaf-spine pair, used/total downlink ports, downlink:uplink ratio per leaf (as configured
and as used), host and fabric cable counts, and transceivers (all-optical, before spares).
(b) Run your lab's `size_two_tier(384, 64, 64, 1.0)`. Explain why its answer differs from (a).
(c) An inference-only variant would accept 3:1. Size it rail-optimized and state the cross-leaf
capacity per leaf against its downlink capacity.
(d) What changes about ECMP's importance in (a) compared with ORION-256?
*Evidence required:* every count with arithmetic; a one-paragraph explanation for (b) and (d).

**7.W2** ★★★ L1 — Using your design from 7.W1(a):
(a) Compute raw uplink, ECMP-aware ingress, and spine-layer bisection capacity (one direction) for
baseline, one leaf-spine link down, and one spine down. Use `fabric_capacity` from the lab and show
the hand arithmetic for at least the ingress values.
(b) Compare the single-link-failure penalty with ORION-256's (Table 7.8) and explain the difference.
(c) Four 400 Gb/s flows are hashed uniformly onto the 4 links between one leaf and one spine.
Compute P(no collision) and the expected number of links used.
*Evidence required:* a results table, formulas with substituted values, and a 3–5 sentence comparison.

---

## Hands-on lab

**7.L** ★★ L1 (L2/L3 extensions) — **Progressive Lab 2: fabric design and validation.** Complete
[lab/README.md](lab/README.md) Tasks 1–6: implement the five functions in
`lab/starter/fabric_lab.py` until `python lab/check.py` reports 19/19 PASS, then write the design
note. **Stretch:** specify (as a written rule plus a five-row test table) a `QOS_MISMATCH` validator
rule covering DSCP trust on host ports, the DSCP→traffic-class map, and the lossless priority, and
state which intent fields it needs that the supplied dataset lacks.
*Evidence required:* checker output (19/19), your findings report, the design note, and (stretch)
the rule specification.

---

## Troubleshooting case

**7.T** ★★★ L1 **[Outline: troubleshoot a scenario involving an MTU mismatch, asymmetric routing, or
incorrect route advertisement using a structured evidence checklist]**

*Evidence pack `[ILLUSTRATIVE]`.* On Thursday at 14:05 a configuration-template update was pushed to
`orion-be-leaf-r1`. From 14:06, a cross-rail benchmark (NCCL with PXN disabled, 16 nodes) shows roughly half
of the connections toward rail-6 NICs failing; NCCL logs contain lines such as:

```text
NET/IB : Got completion from peer 10.100.6.19<41022> with error 12, opcode 0, len 0, vendor err 129 (Recv)
```

(exact format varies by NCCL version; error 12 is `IBV_WC_RETRY_EXC_ERR`: the transport retry
counter was exceeded). Further evidence:

1. `orion-n04$ ping -c 5 -I 10.100.2.9 10.100.6.19` → 100 % loss. `ping -M do -s 8972` → 100 % loss.
   `ping -c 5 -I 10.100.6.9 10.100.6.19` (same rail) → 0 % loss.
2. From `orion-n04`'s rail-3 address to `10.100.6.19`: 0 % loss. From rail 5: 100 % loss.
3. A TCP sweep of 64 source ports from rail 2 to an `iperf3` server on `10.100.6.19`: 31 of 64
   connections never complete the handshake; the failures are the same at 1400-byte and 8948-byte MSS.
4. `orion-be-spine-1# show bgp ipv4 unicast 10.100.6.0/24`:

   ```text
   Paths: (16 available, best #9)
     65102                              <- via 10.101.1.17 (orion-be-leaf-r1), router-id 10.255.0.12, best
     65107                              <- via 10.101.1.97 (orion-be-leaf-r6), router-id 10.255.0.17
     ...
   ```

   `orion-be-spine-2` and `orion-be-spine-4` show the orion-be-leaf-r6 path as best; `orion-be-spine-3` shows the orion-be-leaf-r1 path as best.
5. Interface error counters on every fabric port are zero; every fabric link's MTU matches the intent.
6. `traceroute -n -T -p 41022 -s 10.100.2.9 10.100.6.19` shows `10.100.2.8` (orion-be-leaf-r2) →
   `10.101.1.32` (orion-be-spine-1) → `10.101.1.17` (orion-be-leaf-r1) → `* * *` for the remaining hops.
7. A colleague notes that forward and reverse traceroutes between the two NICs take different spines
   and proposes asymmetric routing as the root cause.
8. `show running-config | include bestpath` on each spine: `orion-be-spine-1` and `orion-be-spine-3`
   print `bgp bestpath compare-routerid` (left over from an older spine template);
   `orion-be-spine-2` and `orion-be-spine-4` print nothing. No spine has `as-path multipath-relax`.

Tasks: (a) Build the evidence checklist (Table 7.9 format) for MTU mismatch, asymmetric routing, and
incorrect advertisement, filling in what each hypothesis predicts and what the pack shows. (b) Rank
the hypotheses and name the root cause. (c) Explain why roughly half of the flows fail and why it is
the rail-2, rail-5 (and not the rail-3) sources that failed in this sample. (d) Respond to the
colleague in item 7. (e) Propose a safe fix, the validation evidence you would collect, and two
preventive controls.
*Evidence required:* a completed checklist table, ranked hypotheses with the discriminating evidence
cited by item number, and a fix/validate/prevent plan with measurable acceptance criteria.

---

## Design challenge

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

---

## Reflection and review

**7.R1** ★ L1 — The lab validates *intent*. List three classes of production fabric fault that an
intent validator can never catch, and for each name the evidence source that would.

**7.R2** ★★ L1 — The capacity model assumes unweighted ECMP and uniform demand. Name two ways a real
fabric could do *better* than the ECMP-aware ingress number and two ways it could do *worse*.

**7.R3** ★★ L1 — Section 7.12's engineer concluded from one successful full-size ping that MTU was
fine. Write the two-sentence rule you would add to the team's troubleshooting guide, and explain the
ECMP reason behind it.

**7.R4** ★ L1 — Which numbers in this chapter are `[MODELED]`, which `[SIMULATED]`, and which
`[ILLUSTRATIVE]`? Give one example of each and say what measurement would upgrade it to `[MEASURED]`.

*Evidence required (R1–R4):* concise written answers; R4 must cite specific numbers from the chapter.

---

## Outline-mandated exercises (index)

| Outline exercise | Where |
|---|---|
| Design a two-tier leaf-spine topology for a specified number of GPU racks and calculate uplink/downlink ratios | 7.W1 (and lab Task 1) |
| Write a conceptual BGP/ECMP routing plan and describe expected behaviour when a link, spine, or leaf fails | 7.O2 below (and lab Tasks 3 and 5) |
| Troubleshoot an MTU mismatch, asymmetric routing, or incorrect route advertisement using a structured evidence checklist | 7.T |

**7.O2** ★★ L1 **[Outline]** — Write a one-page BGP/ECMP routing plan for the ORION-256 backend:
ASN plan, what each tier originates and accepts (with prefix filters), multipath settings
(`maximum-paths` values at leaf and spine with justification), BFD and BGP timers, and the drain
procedure. Then describe, for a **link**, a **spine**, and a **leaf** failure: detection mechanism and
time, routes withdrawn (by whom, which prefixes), resulting ECMP width at an unaffected leaf, capacity
impact (from Table 7.8 or your lab), and workload impact.
*Evidence required:* the plan, a failure table with all five columns for all three failures, and
consistency with your lab's `fabric_capacity` output.

---

## Chapter deliverable

**Topology diagram, routing policy summary, and failure-convergence analysis** for ORION-256 (or
ORION-384 from 7.W1). Submit: (1) a Mermaid or drawn topology diagram showing rails, leaves, spines,
parallel-link counts, ASNs, and loopbacks; (2) the routing policy summary from 7.O2; (3) the
failure-convergence analysis — a table of failure → detection → convergence → capacity →
workload impact, with every capacity number traced to your lab output and labelled `[MODELED]`.
Graded with the lab rubric in [lab/README.md](lab/README.md) §7 (design note portion).
