# Marking scheme: 8.4 RoCEv1 versus RoCEv2

Type knowledge-check · kind written · tier L1 · 5 points

**Evidence required:** encapsulation difference (EtherType vs UDP/IP); routed /31 consequence; at least two counter-level signatures.

| Criterion | Points |
|---|---|
| Encapsulation: RoCEv1 is EtherType 0x8915 with GRH+BTH and no IP header; RoCEv2 is UDP/IP port 4791 | 2 |
| Routed /31 consequence: the leaf cannot route a non-IP frame and drops it | 1 |
| Leaf-side signature (non-IP/unknown-EtherType drops rising, zero DSCP 26/UDP 4791 packets from the port) | 1 |
| Host-side signature (local_ack_timeout_err on both peers, IBV_WC_RETRY_EXC_ERR, no out_of_sequence) | 1 |
