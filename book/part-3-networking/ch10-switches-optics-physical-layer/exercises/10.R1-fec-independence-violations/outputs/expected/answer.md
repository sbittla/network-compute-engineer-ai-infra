# 10.R1 — Why the binomial FEC model in Table 10.1 can be wrong

Table 10.1 (Section 10.4.3) assumes every bit error is independent with the same ratio b, so the
number of bad symbols per codeword is binomial. Two physical mechanisms that violate it:

1. **DFE error propagation.** A decision-feedback equalizer subtracts inter-symbol interference
   using its *previous decisions*. One wrong decision feeds back a wrong correction and makes the
   next symbols more likely to be wrong, producing correlated bursts. **The model underestimates
   uncorrectables** because bursts concentrate many bad symbols in one codeword, crossing the
   t = 15 limit far more often than independent errors at the same average BER would.
2. **Reflections or intermittent mechanical contact** (a damaged or dirty connector, a loose
   module). Reflections superimpose delayed copies of the signal, and a moving contact creates
   short dropouts; both produce error bursts. **The model underestimates uncorrectables** for the
   same reason — this is the signature of lab port Ethernet40 (1,180 uncorrectables at only
   ≈ 0.85 decades of margin, which random errors cannot produce).

Also acceptable: temperature-driven drift or other non-stationary BER (the average hides peaks, so
the model underestimates during the peaks); crosstalk from a neighbouring lane bursting with that
lane's traffic. Codeword interleaving (two codewords per lane symbol stream) partially mitigates
bursts, which is why the model is not useless — it is a lower bound for uncorrectables.

**Operational consequence.** Read the FEC histogram, not just the average BER: populated bins at
12–15 corrected symbols reveal bursts before uncorrectables appear.

**Common wrong answer.** Saying correlation makes the model *overestimate*: burstiness can only move
probability mass into the high-error tail.
