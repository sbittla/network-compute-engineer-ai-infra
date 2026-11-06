# 10.K3 — RS(544,514) parameters

RS(n, k) is a Reed-Solomon code with n symbols per codeword, of which k carry data. KP4 FEC for
100 Gb/s-per-lane Ethernet uses symbols over GF(2¹⁰), i.e. 10-bit symbols (Section 10.4.2).

| Parameter | Formula | Value |
|---|---|---|
| Symbol size | m (GF(2^m)) | **10 bits** |
| Symbols per codeword | n | **544** |
| Parity symbols | n − k = 544 − 514 | **30** |
| Correctable symbols per codeword | t = (n − k)/2 = 30/2 | **15** |
| Codeword size | n × m = 544 × 10 | **5,440 bits** |

**Why t = (n − k)/2.** A Reed-Solomon decoder must find both the location and the value of each
error, which costs two parity symbols per corrected symbol. With 30 parity symbols it corrects up to
15 symbol errors anywhere in the codeword; 16 or more makes the codeword uncorrectable, which is the
threshold used in the binomial model of Table 10.1.

**Corollaries used elsewhere.** Data per codeword = 514 × 10 = 5,140 bits; code rate 514/544 = 0.945
(5.8 % overhead, the 544/514 factor in the 425 Gb/s line rate of a 400G port). A burst of up to 15
consecutive bad symbols (≈ 150 bits) is still correctable because one bad symbol can hold up to 10
bad bits — the reason RS codes tolerate short bursts better than bit-level codes.

**Common wrong answers.** t = 30 (forgetting the factor of 2); codeword size 5,140 bits (data only);
8-bit symbols (that is the classic RS(255,223)).

`solve.py` derives the five values from n, k and m and asserts them `[MODELED]`.
