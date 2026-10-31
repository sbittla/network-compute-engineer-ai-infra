# 2.1.2 — Three networks, three failure effects

Source: manuscript Section 2.4 ("The three networks and their bill of materials").

1. **Backend (compute) fabric**, the rail-optimized 400G RoCEv2 network: total loss makes every
   collective unable to complete, so a running multi-node training job hangs in NCCL until its timeout
   fires and then fails. It restarts from the last checkpoint only after the fabric returns. Single-node
   jobs continue.
2. **Frontend/storage network**, 2 × 200 GbE per node: jobs stall at the next dataset read or checkpoint
   write (the step blocks in the data loader or the checkpoint call), schedulers and logins become
   unreachable, and the inference service is unreachable by its clients even though the GPUs are healthy.
3. **Out-of-band (OOB) management network**, 1 GbE to every BMC, PDU and switch management port: running
   work is unaffected, but operators lose remote power control, serial console, BMC sensors and
   firmware management. A node that hangs during the outage cannot be power-cycled remotely, so the
   outage turns every later fault into a hands-on visit.

The answer shows why the OOB network is often accepted as a lower-redundancy design (no immediate job
impact) while the frontend leaves need dual-homing and dual power (see the lab's `pdu-net-A` SPOF).
