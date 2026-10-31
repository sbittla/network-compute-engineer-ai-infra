# 10.K2 — Why a healthy 400G PAM4 link counts FEC corrections

**Model answer (≤ 120 words).** PAM4 carries 2 bits per symbol on four amplitude levels, so its three
eyes each get one third of the amplitude an NRZ eye would have: the SNR penalty is
20·log10(3) ≈ **9.5 dB**. At 53.125 GBd per lane over real channels, a healthy link therefore runs at
a raw (pre-FEC) BER of roughly 10⁻⁸ to 10⁻⁵. The standard makes RS(544,514) "KP4" FEC mandatory; it
corrects up to 15 symbols per codeword and counts every codeword it repairs, so the corrected counter
rises continuously by design. A 10G NRZ link has enough SNR to run at ≈ 10⁻¹² or better without
mandatory FEC, so its error counters stay at zero.

**Supporting arithmetic** `[MODELED]`. Amplitude ratio 1/3 → 20·log10(3) = 20 × 0.477 = 9.54 dB.
Table 10.1 (Section 10.4.3) shows why corrected codewords are harmless: at a pre-FEC BER of 10⁻⁵ the
probability that a codeword is uncorrectable is ≈ 2 × 10⁻³⁴, so the link is effectively error-free
after FEC.

**What to monitor instead.** Not the corrected count, but the pre-FEC BER margin to 2.4 × 10⁻⁴ in
decades, its trend, and any non-zero uncorrectable count (Section 10.4.3).

**Common wrong answer.** "PAM4 links are lower quality." They are engineered to operate at this BER;
the FEC is part of the link budget, not a repair for a bad link. Another frequent slip is quoting
6 dB (the penalty for 2× amplitude), which is the wrong ratio: PAM4 has three eyes stacked, not two.
