# Chapter 18 — Exercises

Difficulty: ★ foundational · ★★ intermediate · ★★★ advanced. Tier: L1 laptop/paper · L2 one GPU
host · L3 multi-node with RDMA and switch access. Every exercise states the evidence required for
grading. Answers and marking guidance are in `solutions/exercises-key.md` (instructors).

**Chapter deliverable (course outline):** an **SLO specification** (Exercise M1), a **dashboard
mock-up** (Exercise M2), and a **blameless postmortem** (Exercise M3 / Lab 18).

---

## Knowledge checks

**K1 ★ L1 — The lying utilization metric.** Explain the mechanism by which `DCGM_FI_DEV_GPU_UTIL`
stays near 97 % while a training job is stalled waiting on the network. Name two DCGM metrics and one
non-DCGM signal that would reveal the stall.
*Evidence required:* a definition of what GPU_UTIL measures; the role of NCCL kernels; three named
signals with one sentence each on why they move.

**K2 ★ L1 — Why polling fails at 400 Gb/s.** (a) How often does a 32-bit octet counter wrap at
400 Gb/s line rate? (b) What utilization does a 2 ms line-rate burst show when averaged over a 60 s
poll? (c) What is the maximum duration of a single PFC pause frame at 400 Gb/s?
*Evidence required:* each calculation with formula, substitution, and units.

**K3 ★ L1 — Throughput vs goodput.** Define the training throughput SLI and the training goodput SLI
of Table 18.4. Describe a week in which throughput SLI is 100 % but goodput is 80 %.
*Evidence required:* both definitions as good/valid ratios; a numeric example that produces 80 %.

**K4 ★★ L1 — Two windows.** In a multiwindow burn-rate alert, what failure of a single-window alert
does the long window prevent, and what failure does the short window prevent?
*Evidence required:* one concrete scenario for each window.

**K5 ★ L1 — Who is pausing whom?** A backend host's `ethtool -S` shows `rx_prio3_pause` rising fast and
`tx_prio3_pause` flat. Another host shows the opposite. Interpret each.
*Evidence required:* direction of the pause for each host and the likely location of the bottleneck.

**K6 ★ L1 — Incident roles.** Why should the incident commander not debug hands-on? What does the
communications lead publish, and how often, for a SEV2 on ORION?
*Evidence required:* two reasons; cadence from Table 18.8; one example status update.

**K7 ★ L1 — Timeline arithmetic.** Define TTD, TTM, and TTR. Why must onset come from telemetry rather
than from the first report?
*Evidence required:* three definitions; one sentence on the bias introduced by human-reported onset.

**K8 ★★ L1 — Cardinality.** Why must `rank`, `request_id`, and `step` never be Prometheus labels on
high-frequency metrics? Estimate the series count if a 4,096-GPU job exported a per-rank step-time
gauge with a `step` label for one day at 17.4 s per step.
*Evidence required:* the series-count calculation and where that information should live instead.

## Worked problems

**W1 ★★ L1 — Error budget and burn rate.** `chat-70b` has a 99.9 % availability SLO over 30 days and
serves an average 3,000 requests per minute.
(a) Compute the budget in failed requests and in equivalent minutes of total outage.
(b) A bad config causes 0.6 % errors for 90 minutes. Compute the burn rate and the fraction of budget
consumed. Does either page condition of Table 18.5, or the ticket condition, fire during those 90
minutes?
(c) Repeat for 2 % errors for 90 minutes; if a page fires, when (minutes after onset, including
`for: 2m`)?
(d) At the burn rate of (b), how long until the budget is exhausted?
*Evidence required:* every formula, substitution, and result; a yes/no with the window values for each
alert condition.

**W2 ★★★ L1 — Is a 9 % regression worth a page?** A 4,096-GPU ORION-XL job's step time rises from
17.4 s to 19.0 s because of a fabric problem.
(a) Compute the throughput ratio and the fraction of GPU time lost.
(b) Case A: nobody notices for 6 h; mitigation takes another 30 min. Case B: an alert detects it in
12 min; mitigation takes 30 min. Compute lost GPU-hours and cost at $3 per GPU-hour for each.
(c) Would ORION's `TrainingThroughputFastBurn` rule (threshold 1.10 × baseline) fire? If not, propose
a threshold for jobs above 1,024 GPUs and state the evidence you would need that it will not be noisy.
*Evidence required:* arithmetic for (a)–(b); a justified threshold for (c) with a noise argument.

## Hands-on lab

**L1 ★★ L1 — Lab 18: telemetry-bundle forensics** ([lab/README.md](lab/README.md)). Implement every
function in `lab/starter/telemetry_analysis.py`, pass `python check.py`, and submit the deliverables
of the lab README Section 8.
*Evidence required:* checker output with 14/14 PASS; `postmortem.md`; `dashboard_spec.json`;
`slo_spec.md`.

## Troubleshooting case

**T1 ★★★ L1 — The TTFT page.** At 20:05 `ChatTTFTFastBurn` pages for `chat-70b` (8 replicas, TP = 8,
one replica per HX8 node). Evidence `[ILLUSTRATIVE]`:

```text
20:00  TTFT p95 0.62 s → 20:04 1.9 s;  TPOT p95 flat at 38 ms;  5xx rate 0.01 % (normal)
20:00  request rate 3,050/min → 20:04 3,120/min (normal evening growth)
vllm:num_requests_waiting   replicas 0-6: 0-2 → 20:04: 35-48      replica 7: series absent since 19:58
kube_pod_container_status_restarts_total{pod="chat-70b-7"}  3 → 6 between 19:55 and 20:04
kubectl describe pod chat-70b-7:  Last State: Terminated  Reason: OOMKilled  Exit Code: 137
DCGM_FI_DEV_FB_USED replica 7 (before restart): 79.1 GiB of 79.6 GiB
events: 19:52 DEP-44 "chat-70b: raise max context length to 32k for enterprise tier" (rev 44)
fabric: normal; storage: normal; GPU Xid: none
```

Walk the diagnostic loop: rank hypotheses, name the discriminating evidence for each, state the root
cause, the mitigation you would take first, and how you would validate. Explain why TPOT is flat while
TTFT explodes.
*Evidence required:* ranked hypothesis table; root cause tied to specific lines above; mitigation +
validation criteria; the TTFT/TPOT explanation.

## Design challenge

**D1 ★★★ L1 — Alerting for ORION-XL on one rotation.** ORION-XL runs ≈ 40 concurrent training jobs
(64 to 4,096 GPUs) and three inference services, with one SRE rotation whose page budget is two
incidents per 12-hour shift. Design the page-severity alert set (≤ 8 rules), the ticket set, and the
routing. Defend which causes, if any, are allowed to page, and how you prevent 40 jobs from producing
40 pages during one fabric incident.
*Evidence required:* rule table (name, SLI or cause, windows/thresholds, severity, route); grouping /
inhibition strategy; estimated pages per shift with assumptions.

## Reflection / review

**R1 ★ L1** — Which conclusions in your lab postmortem are *proven* by the bundle and which are only
*correlated*? What additional evidence would convert a correlation into proof?

**R2 ★★ L1** — The lab's switch telemetry is one-minute per-switch aggregates. Which parts of the root
cause could you not establish with that resolution, and what telemetry would you add?

**R3 ★★ L1** — List three ways the training throughput SLI could be gamed or mislead (e.g. baseline
drift) and a guard against each.

**R4 ★ L1** — What evidence in a postmortem shows that it is blameless? Rewrite one blaming sentence
from your own experience (or invent one) in blameless form.

*Evidence required (R1–R4):* concise written answers, each referencing a specific data file, metric,
or section.

## Outline-mandated exercises

**M1 ★★ L1 — SLI/SLO specification.** Define SLIs and SLOs for **training job completion**, **inference
latency**, **cluster availability**, and **fabric health** for ORION. For each: good/valid events,
measurement source and query, SLO and window, error budget (with arithmetic), burn-rate alert policy,
and the owner. *(Deliverable: `slo_spec.md`.)*
*Evidence required:* a table covering all four services; at least one PromQL recording rule per SLI;
budget arithmetic; exclusions (e.g. client 4xx, user-code failures) stated.

**M2 ★★ L1 — Dashboard hierarchy.** Design the dashboard hierarchy from **fleet overview to node, GPU,
NIC, switch, and workload detail**. For each level: the one question it answers, 4–8 panels with
query and unit, and the drill-down key to the next level. Include a mock-up sketch (ASCII or image) of
the fleet level. *(Deliverable: dashboard mock-up; `dashboard_spec()` in the lab is the machine-checked
skeleton.)*
*Evidence required:* level table; mock-up; drill-down keys; justification of two panels you rejected.

**M3 ★★★ L1 — Incident timeline and postmortem for a cluster-wide throughput regression.** Using the
Lab 18 bundle, write the incident timeline (onset, detection, declaration, mitigation, resolution with
TTD/TTM/TTR) and a blameless postmortem from the template, including impact with evidence labels,
rejected hypotheses with the evidence that rejected them, and ≥ 5 action items typed detect /
mitigate / prevent with owners. *(Deliverable: `postmortem.md`.)*
*Evidence required:* timeline table; postmortem; checker PASS on T5.
