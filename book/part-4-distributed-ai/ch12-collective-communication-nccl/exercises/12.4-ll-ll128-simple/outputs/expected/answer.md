# 12.4 — NCCL protocols: payload efficiency vs latency

Section 12.6, Table 12.4 `[VENDOR-SPEC, 2026-10]`.

| Protocol | Payload efficiency | Latency | Why it costs what it costs |
|---|---|---|---|
| LL (low latency) | ≈ 50 % (4 B data + 4 B flag in each 8-byte store) | Lowest | Data and a flag travel in the *same* 8-byte atomic store, so the receiver polls the flag and knows the data beside it is valid: no separate memory fence or synchronization round trip. Half of every store is flag, so bandwidth is halved. |
| LL128 | ≈ 94 % (120 B data + 8 B flag per 128-byte line) | Low | The same flag trick at 128-byte granularity; it relies on 128-byte stores arriving whole and in order, which NVLink-class paths guarantee but not every PCIe/network path, so NCCL enables it only where that holds. |
| Simple | ≈ 100 % | Highest | Bulk data in large chunks, then a memory fence and a flag write per chunk; the receiver waits for the flag. The fence and handshake add several µs per step, invisible for large messages, dominant for small ones. |

**Consequence for tuning.** NCCL picks LL for small messages (latency-bound), LL128 for medium sizes on
NVLink, and Simple for large messages (bandwidth-bound). Forcing `NCCL_PROTO=Simple` therefore leaves
the plateau unchanged but raises small-message latency — one of the hypotheses in Exercise 12.14.
Forcing LL on large messages halves the achievable busbw.

**Common wrong answers.** "LL is lossy" (it is not; it trades bandwidth for latency); quoting LL128
as 100 %; saying Simple is slower because it copies more data (it copies the same data; it
synchronizes more).
