# 14.8 result `[MODELED]`

(a) S = 34e9 × 14 B = 476 GB; per GPU 3.72 GB
(b) write = 476 / 40 = 11.9 s; blocking = 12.9 s
(c) overhead = 12.9 / 900 = 1.43 %
(d) RPO max = 900 + 12.9 = 912.9 s; E[lost] = 450 + 12.9 = 462.9 s
(e) async: overhead 0.067 % (0.11 % with interference); L = 13.5 s; RPO max = 913.5 s (unchanged)
(f) tau = 300 - 13.5 = 286.5 s; delta = 0.987 s; overhead = 0.34 %
