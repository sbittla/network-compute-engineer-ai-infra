# Marking scheme: 8.1 Keys and access rights

Type knowledge-check · kind written · tier L1 · 5 points

**Evidence required:** correct definitions; the failing check and the completion status; resulting QP state.

| Criterion | Points |
|---|---|
| Correct definitions: lkey authorizes the local NIC in a local SGE; rkey authorizes the peer's remote access within the MR flags | 2 |
| Failing check named (target NIC validates rkey/access rights, MR lacks IBV_ACCESS_REMOTE_WRITE, NAK) and the initiator CQE IBV_WC_REM_ACCESS_ERR | 2 |
| Initiator QP moves to ERROR; later WRs flush with IBV_WC_WR_FLUSH_ERR | 1 |
