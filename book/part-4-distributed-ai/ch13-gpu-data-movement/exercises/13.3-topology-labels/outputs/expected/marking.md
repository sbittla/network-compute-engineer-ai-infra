# Marking scheme: 13.3 Topology labels PIX, PXB, PHB, NODE, SYS

Type knowledge-check · kind written · tier L1 · 5 points

**Evidence required:** five definitions; answer labelled `[VENDOR-SPEC, YYYY-MM]`

| Criterion | Points |
|---|---|
| PIX and PXB defined correctly (one switch; several switches without crossing a host bridge) | 2 |
| PHB, NODE and SYS defined correctly (host bridge; across host bridges within one NUMA node; inter-socket link), with GPU 0 <-> NIC 2 on ORION identified as NODE (PHB accepted if justified) | 2 |
| States NCCL default uses GDR up to about PXB, so NODE/SYS pairs are host-staged, labelled [VENDOR-SPEC, 2026-10] with a verify note | 1 |
