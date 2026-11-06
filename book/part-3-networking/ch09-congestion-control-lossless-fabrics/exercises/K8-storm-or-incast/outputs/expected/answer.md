# K8 — PFC storm or incast? (worked solution)

Relies on manuscript Section 9.8 (Table 9.6, Figure 9.10) and Section 9.5 ("PFC storms and the
slow-receiver symptom"). Values below are the signatures on the **switch port facing the device**, with
the lab's episode medians as `[SIMULATED]` examples.

| Signal on the port facing the device | PFC storm source (device emits pause) | Incast destination (device receives N:1) |
|---|---|---|
| TC 3 egress queue | **Flat at maximum** (≈ 4,000 KB in the lab), not draining | **Deep but varying** (≈ 1,100–1,700 KB, held near Xoff by PFC) |
| Egress throughput toward the device | **≈ 0 Gb/s** (0.03 Gb/s) | **≈ line rate** (≈ 394 Gb/s) |
| ECN marks on that queue | **≈ 0**: nothing leaves, so nothing is marked | **Present**: heavy on a template leaf; on the lab's as-found leaf only on peaks above Kmin (median 0, up to ≈ 90 k/s) |
| Pause *received* from the device (`pfc_rx_p3`) | **Sustained**, thousands/s (≈ 23,700/s) | **≈ 0**: the NIC is draining fine |
| Device's own receive throughput | ≈ 0 | ≈ line rate |
| Device NIC counters | `pfc_tx_p3` ≈ the switch's `pfc_rx`; no CNPs | `np_cnp_sent` tracks the marks (low on the as-found leaf, high on a template leaf); no pause tx |

Any four rows with both values earn full marks. The decisive pair is egress ≈ 0 with sustained pause
received (storm) against egress at line rate with no pause received (incast root).

**Common mistake:** "deep queue" as a discriminator on its own: both cases have one.
