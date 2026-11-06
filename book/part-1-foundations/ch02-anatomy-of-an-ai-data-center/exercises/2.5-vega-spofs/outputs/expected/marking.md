# Marking scheme: 2.5 Five single points of failure

Type outline-mandated · kind written · tier L1 · 15 points

**Evidence required:** SPOF table (component, impact, mitigation, fix/accept, reason); failure-domain diagram; answer to task 4.

| Criterion | Points |
|---|---|
| At least five correct SPOFs, each with its service impact (for example network-rack single PDU, border router, load balancer, NFS weight server, control plane on one host, DNS/NTP VM) | 6 |
| Failure-domain diagram showing which components share a host, rack, PDU or feed | 3 |
| A mitigation per SPOF with a fix or accept decision justified by cost, likelihood or recovery time | 4 |
| Task 4 names a placement SPOF (the three control-plane VMs on one hypervisor, or the single-feed network-rack PDU) | 2 |
