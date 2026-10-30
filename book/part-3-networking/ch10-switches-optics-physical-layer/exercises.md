# Chapter 10 — Exercises

Difficulty: ★ foundational · ★★ intermediate · ★★★ advanced. Tier: L1 (laptop/paper), L2 (one host
with a NIC), L3 (lab switch + hosts). Every exercise states the evidence required for grading. Values
are `[ILLUSTRATIVE]` unless labelled otherwise; show formula → substitution → result with units.

Exercises marked **(Outline)** are mandated by the course outline; **10.M4** is the chapter
deliverable.

---

## A. Knowledge checks (★, L1)

**10.K1** Name the switch-ASIC pipeline stage (SerDes/PMD, PCS/FEC, MAC, traffic manager) at which
each counter is produced: (a) Rx optical power, (b) FEC-uncorrectable codewords, (c) FCS errors,
(d) output discards, (e) PFC pause frames sent, (f) oversize (giant) frames.
*Evidence required:* a six-row table: counter → stage → one-line justification.

**10.K2** Why does a healthy 400G PAM4 link show a continuously increasing FEC-corrected codeword
counter, while a healthy 10G NRZ link typically shows no errors at all?
*Evidence required:* ≤ 120 words naming the PAM4 SNR penalty (with its dB value) and the role of FEC.

**10.K3** State the RS(544,514) parameters: symbol size, symbols per codeword, parity symbols,
correctable symbols per codeword, and codeword size in bits.
*Evidence required:* five values with the arithmetic for the correctable-symbol count.

**10.K4** Explain "CRC stomping". On a cut-through fabric, why can a perfectly healthy link report
FCS errors, and which counter on which device localizes the real fault?
*Evidence required:* ≤ 150 words plus the name of the localizing counter.

**10.K5** Compare 400GBASE-DR4 and 400GBASE-FR4: medium, connector, number of fibers used,
wavelengths, and reach. Can a DR4 module link to an FR4 module? Why or why not?
*Evidence required:* a comparison table and a one-sentence answer with the reason.

**10.K6** List five DOM quantities a CMIS module reports and, for each, one failure it helps detect.
*Evidence required:* five rows: quantity → failure → what you compare it against.

**10.K7** Why is a miscabled-but-error-free uplink on ORION's /31 eBGP fabric a capacity problem, and
why does no physical-layer error counter detect it?
*Evidence required:* ≤ 120 words; name the check that does detect it.

---

## B. Worked problems

**10.W1 — Link budget for a cross-hall DR4 link (★★, L1).**
Halcyon AI adds a second data hall. A 400G-DR4 link runs 420 m over SMF with four mated MPO pairs
(two patch panels per hall) and two fusion splices. Assume 0.4 dB/km, 0.5 dB per mated MPO pair,
0.1 dB per splice; DR4 worst-case Tx −2.9 dBm per lane, receiver minimum −5.9 dBm average per lane,
maximum channel insertion loss 3.0 dB (`[VENDOR-SPEC, 2026-10]`, IEEE 802.3bs; verify).
(a) Compute channel loss, worst-case Rx power, and margin. (b) One MPO pair is dirty and adds 1.0 dB.
Does the link still meet the channel budget and the receiver minimum? (c) Convert the answer to (a)'s
Rx power to mW. (d) In service, all four lanes read Rx −4.1 dBm while the far end reports Tx +0.6 dBm
on every lane. Compute measured and excess loss and state where you look first.
*Evidence required:* every formula, substitution, and result in dB/dBm/mW; a one-sentence decision for
(b) and (d).

**10.W2 — FEC arithmetic and sparing at ORION-XL scale (★★★, L1).**
(a) An 800G port uses eight 100G lanes with the same 256b/257b + RS(544,514) overheads as 400G.
Compute the line rate and the codeword rate. (b) A port runs at pre-FEC BER 2 × 10⁻⁵. Compute its
margin in decades to 2.4 × 10⁻⁴ and estimate the fraction of codewords that contain at least one
symbol error (use the symbol error probability p ≈ 10 × BER and P(≥1) = 1 − e^(−544p)). (c) ORION-XL
has 16,384 backend optics with an AFR of 1.5 % and a 21-day resupply lead time. Using a Poisson model,
how many spares give ≥ 95 % and ≥ 99 % probability of not running out during one lead time?
(d) Explain why the rate-based policy (3 %) gives a much larger number, and when you would use each.
*Evidence required:* formulas and numbers for (a)–(c) (a table of cumulative Poisson probabilities is
acceptable); ≤ 120 words for (d).

---

## C. Hands-on lab (★★–★★★, L1; L2/L3 extensions)

**10.H1 — Link-health analyzer and commissioning report.** Complete [lab/README.md](lab/README.md)
tasks 1–8 for `orion-be-leaf-r3`.
*Evidence required:* `python check.py` output showing `13/13 checks passed`; the generated
`commissioning-report.md`; `diagnosis.md` explaining every non-healthy port (evidence, layer, root
cause hypothesis, first safe action, missing hardware evidence) and every decoy you identified.

---

## D. Troubleshooting case (★★★, L1)

**10.T1 — "Leaf r6 uplinks are dirty" (incomplete evidence).**
An automated alert says `orion-be-leaf-r6:Ethernet33`–`Ethernet40` (all eight uplinks to spine-1) show
rising output discards and PFC pause frames received. They rise only during the 20-minute nightly
run of an MoE evaluation job whose expert-parallel all-to-all crosses rails through the spines
(Chapter 12); backend training traffic otherwise stays on its rail, and checkpoints use the
frontend/storage NICs. A colleague files a ticket to clean all eight uplinks. You have: discards and
PFC counters for those eight ports (rising only between 01:00 and 01:20), FEC-uncorrectable = 0 and FCS = 0 on all eight,
pre-FEC BER 10⁻⁸–10⁻⁷, DOM normal. You do **not** have spine-side counters or host-side counters.
(a) Is this physical? Apply the five discriminating questions of Section 10.8.1. (b) What evidence
is missing, and how would you collect it safely? (c) Who owns the next step, and what do you write on
the cleaning ticket?
*Evidence required:* the five questions answered from the given evidence; a list of ≥ 3 missing items
with the command or data source for each; a two-sentence ticket update.

---

## E. Design challenge (★★★, L1)

**10.D1 — Media plan for ORION's expansion pod.** Halcyon adds a 16-node pod. The new rail leaves sit
in a network rack 3 m from the new spines; the GPU racks are 25–40 m from the network rack; the pod
must connect to the existing spines in the old hall 350 m away. Choose a medium (DAC, AEC, AOC, SR8,
DR4, FR4) for (i) host links, (ii) new leaf ↔ new spine, (iii) new spine ↔ old spine/super-spine, and
choose single-port vs twin-port switch modules. Defend each choice on reach, power, failure modes,
sparing, and cleaning burden, and state what you would verify with the vendors.
*Evidence required:* a decision table (link class × medium × reason), an optics-power estimate with
stated per-module power, and the spare-part list implied by your choices.

---

## F. Reflection and review (★–★★, L1)

**10.R1** The binomial FEC model in Table 10.1 assumes independent errors. List two physical
mechanisms that violate it and the direction in which each biases the model.
*Evidence required:* two mechanisms, each with "model underestimates/overestimates uncorrectables
because…".

**10.R2** The lab's thresholds are `[ILLUSTRATIVE]`. Describe how you would set real warning
thresholds for pre-FEC BER and Rx power on a new fleet, and what data you would need.
*Evidence required:* ≤ 150 words naming the data sources (commissioning baselines, vendor
thresholds, failure history).

**10.R3** What can the L1 lab *not* tell you about `orion-be-leaf-r3` that an L3 commissioning run
would? Name at least four items.
*Evidence required:* four or more items, each tied to a physical mechanism.

**10.R4** Your analyzer marks a port "healthy" that later causes an incident. Name two ways a
two-snapshot method can miss a real fault, and how you would change the collection.
*Evidence required:* two failure modes of the method and one design change each.

---

## G. Outline-mandated exercises and deliverable

**10.M1 (Outline) — Link commissioning checklist (★★, L1; L3 to execute).**
Create a link commissioning checklist covering **port configuration, transceiver compatibility,
optical power, lane health, error counters, and cable labeling** for ORION's backend links. For each
item give: what to check, the exact evidence source (command, telemetry path, or record), the pass
criterion with a number where applicable, and what to do on failure.
*Evidence required:* a checklist table with all six required areas present, numeric pass criteria for
optical power, lane health, and error counters, and a stated soak duration.

**10.M2 (Outline) — Interpret counters: physical or higher-layer? (★★, L1).**
The table below shows hypothetical deltas over 600 s for six 400G-DR4 ports on one leaf (pre-FEC BER
and Rx power are T1 values; "BER 7 days ago" is from the baseline). Classify each port as physical or
higher-layer, give the most likely cause, the first safe action, and one further piece of evidence you
would collect.

| Port | Link-down events | FEC corrected CW | FEC uncorr. CW | FCS errors | Symbol errors | Giants | Out discards | PFC pause tx | Pre-FEC BER (now / 7 days ago) | Rx power per lane (dBm) |
|---|---|---|---|---|---|---|---|---|---|---|
| P1 | 0 | 3.1 × 10⁷ | 0 | 0 | low | 0 | 52,410 | 1.1 × 10⁶ | 1.2e-7 / 1.1e-7 | −1.1, −1.3, −0.9, −1.2 |
| P2 | 0 | 8.6 × 10⁹ | 340 | 322 | high | 0 | 0 | 0 | 4.0e-5 / 3.6e-5 | −2.0, −2.1, −1.9, −2.0 |
| P3 | 0 | 5.1 × 10⁶ | 0 | 1,870 | ≈ 0 | 0 | 0 | 0 | 2.0e-8 / 2.1e-8 | −0.8, −0.7, −0.9, −0.8 |
| P4 | 5 | 2.0 × 10⁷ | 12 | 9 | low | 0 | 0 | 0 | 8.0e-8 / 7.5e-8 | −1.4, −1.5, −1.3, −1.6 |
| P5 | 0 | 1.9 × 10¹⁰ | 0 | 0 | high | 0 | 0 | 0 | 9.0e-5 / 2.0e-6 | −6.8, −2.1, −2.0, −2.2 |
| P6 | 0 | 2.6 × 10⁶ | 0 | 0 | ≈ 0 | 12,044 | 0 | 0 | 1.0e-8 / 1.0e-8 | −0.5, −0.6, −0.4, −0.5 |

*Evidence required:* a six-row answer table (layer, cause, first action, further evidence) and, for
P2 and P5, the FEC margin in decades with arithmetic.

**10.M3 (Outline) — Ports, cables, and spares for a small leaf-spine fabric (★★, L1).**
A 24-node HX8 pod (8 GPUs and 8 × 400G backend NICs per node), rail-optimized, 1:1, 64-port 400G
switches, 400G-DR4 on every link. Estimate: leaves, spines, uplinks per leaf per spine, host links,
fabric links, optics, cables, leaf and spine ports used and free, and spares (3 % optics, 2 % cables,
minimum 2 per type, one spare switch per model). Identify the operational spares beyond optics and
cables. What happens to the spine layer if the pod grows to 32 nodes?
*Evidence required:* every quantity with its formula; a spares list; ≤ 80 words on growth. You may
check your numbers with the lab's `estimate_fabric_bom()`.

**10.M4 (Deliverable) — Physical-layer runbook and port/cabling schedule (★★★, L1).**
For the lab's `small` fabric (16 nodes), deliver (a) a **port/cabling schedule** (CSV) generated by
your `generate_cabling_schedule()`, with cable IDs, both endpoints, optic types, label text, and a
length column you fill from a stated rack layout; and (b) a **physical-layer runbook** (≤ 3 pages)
containing: signal → threshold → first safe action → escalation table; a drain-before-touch procedure
for host links and for uplinks; the commissioning gates; the cleaning/inspection procedure; and the
sparing policy with numbers.
*Evidence required:* the CSV (row count = 256, unique IDs) and the runbook; the runbook must cite
which thresholds are `[ILLUSTRATIVE]` policy and which come from a specification.
