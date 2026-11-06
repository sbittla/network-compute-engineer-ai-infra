# R3 — Proof versus correlation in Section 9.12 (model answer)

Relies on manuscript Section 9.12 ("The rail that ran on pause frames": `orion-n18`'s rail-6 NIC
trained at PCIe x8 after Tuesday's maintenance, pausing its leaf port) and docs/VERIFIED_FACTS.md
(PCIe Gen5 achievable bandwidth). Evidence `[ILLUSTRATIVE]`.

## Evidence that proves the root cause

1. **The hardware state:** `lspci -vv` shows `LnkSta: Speed 32GT/s, Width x8 (downgraded)` while
   `LnkCap` is x16. That is a direct observation of the fault.
2. **Quantitative agreement:** the port's steady egress of **≈ 213 Gb/s** matches what PCIe Gen5 x8
   delivers (≈ 252 Gb/s raw, ≈ 200–220 Gb/s achievable after protocol overhead). A healthy x16 link
   would sustain line rate.
3. **Pause originates at that NIC:** its own `tx_prio3_pause` counter rises, and leaf port `eth1/18`
   *receives* pause from it while transmitting ≈ 213 Gb/s. That is the slow-receiver signature, as
   opposed to a storm (≈ 0 Gb/s) or incast (line rate, no pause from the NIC).
4. **The loop is closed by intervention:** after the fix (reseat → x16) the pauses stop and step time
   returns to the 17.4 s baseline. Changing only the suspected variable removes the symptom, and that
   is what turns a strong hypothesis into a proven cause.

## Evidence that is merely correlated

- **Timing:** the slowdown began after Tuesday's maintenance. Many things changed in that window.
- **Victim senders' pauses:** the senders paused by the leaf are a *consequence* of the slow receiver,
  not evidence of its cause, and they would look the same for other root causes.
- **The job-level slowdown** (17.4 → 19.9 s step, +14 %): it could have other contributors (GPU
  throttling, stragglers) until the post-fix validation shows that the whole difference is recovered.
