# K2 — Why polling fails at 400 Gb/s

Line rate 400 Gb/s = 400 × 10⁹ / 8 = 50 × 10⁹ B/s. `[MODELED]`

**(a) 32-bit octet counter wrap.** 2³² B = 4,294,967,296 B.
t_wrap = 4.295 × 10⁹ B / 50 × 10⁹ B/s = **0.086 s**: the counter wraps ≈ **11.6 times per second**,
so a 60 s SNMP poll cannot tell how many times it wrapped. Only 64-bit counters (`ifHCInOctets`,
OpenConfig `in-octets`) are usable.

**(b) 2 ms line-rate burst over a 60 s poll.** Burst bytes = 50 × 10⁹ B/s × 0.002 s = 1 × 10⁸ B
(100 MB). Poll capacity = 50 × 10⁹ B/s × 60 s = 3 × 10¹² B. Utilization = 1 × 10⁸ / 3 × 10¹² =
3.3 × 10⁻⁵ = **0.0033 %**. The burst that filled a buffer and triggered PFC is invisible in the
average; you see it only in queue watermarks, ECN marks, and pause counters.

**(c) Maximum single PFC pause.** The pause timer is 16 bits of quanta, each 512 bit times:
65,535 × 512 bit = 33,553,920 bit; / 400 × 10⁹ b/s = **83.9 µs**. A switch that keeps pausing must
therefore refresh pause frames continuously; a long pause shows up as many frames and a growing
pause-duration counter.

**Common mistake:** using 400 GB/s instead of 400 Gb/s (an 8× error). Source: Section 18.4 ("Switch
telemetry: why streaming replaced polling"). `solve.py` reproduces all three.
