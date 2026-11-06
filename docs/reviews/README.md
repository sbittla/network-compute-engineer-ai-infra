# Pre-publication technical reviews (2026-11-05)

Seven specialist reviews of the print (concise) edition, with the full-length manuscripts, labs and
capstones where the finding touched them. **These reviews were AI-assisted.** They are not the
independent review by external human specialists that the release gates call for; that review is
recorded separately (see [RELEASE_READINESS.md](../RELEASE_READINESS.md), item 3).

Every reviewer recomputed the chapter's main models from its stated inputs, audited evidence labels,
checked that ORION reads as illustrative, checked diagrams against the prose and checked lab safety.
Definite errors were fixed in both editions within the print edition's 4,000-word chapter cap.

| Review | Chapters | Findings | Fixed | Accepted or deferred | Log |
|---|---|---|---|---|---|
| GPU systems | 1, 3, 4, 5, 6 | 15 (1 major, 14 minor) | 12 | 3 | [gpu-systems.md](gpu-systems.md) |
| Networking and RDMA | 7, 8, 9, 10 | 12 (1 major, 11 minor) | 12 | 0 | [networking-rdma.md](networking-rdma.md) |
| Distributed training and storage | 11, 12, 13, 14 | 17 (1 major, 9 minor, 7 info) | 11 (+1 confirmed) | 5 | [distributed-training-storage.md](distributed-training-storage.md) |
| Inference serving | 15, Capstones D and H | 19 (5 medium, 9 low, 5 info) | 12 | 7 (2 accepted, 5 info needing no change) | [inference-serving.md](inference-serving.md) |
| Operations, reliability, security | 16–20 and their labs | 15 (7 medium, 7 low, 1 verified-not-an-error) | 13 | 2 | [operations-security.md](operations-security.md) |
| Facilities, economics, capstones | 2, 21, 22, 23, 24, all capstones | 11 (2 major, 8 minor, 1 info) | 10 | 1 (author decision) | [facilities-economics-capstones.md](facilities-economics-capstones.md) |
| Sources, versions, bibliography | Appendix E, reading list, VERIFIED_FACTS | E.13 resolved, 0 of 102 links dead | all | 3 claims stay unverified (Table E.14), hedged in text | [sources-versions.md](sources-versions.md) |

No reviewer found a wrong number in a worked model except where noted in its log; the majors were
an inconsistency (ch09 PFC headroom sized for 30 m against 45–50 m host runs), a contradiction
(ch03 GPU utilisation), a missing concept (ch11 elastic relaunch) and two clarity gaps (fictional
setting not stated in the capstones; TCO prices read as quotes).

## Release-editor decisions on the items left open

| Item | Decision |
|---|---|
| G10, G11 (ch06 simulated data uses PyTorch 2.4/2.3 and 570/575 drivers) | Accepted. They are fields in a fixed, seeded teaching dataset labelled `[SIMULATED]`/`[ILLUSTRATIVE version]`; the lesson (a stale container skews results) does not depend on the version numbers. Refresh with the next dataset regeneration. |
| G12 (REFERENCE_CLUSTER software baseline) | Fixed: aligned with Appendix E. |
| G13 (NCCL GDR log level) | Fixed in VERIFIED_FACTS by the sources review. |
| G14 (no Appendix E rows for Nsight flags) | Fixed: rows added; ch04 corrected for the Nsight Compute 2026.1 clock-lock default. |
| G15 (PHB vs NODE for a NIC on another root port) | Accepted with note: the class depends on the platform's host-bridge layout; the lab data uses PHB and the chapter tells readers to read their own `nvidia-smi topo -m`. |
| DT-11 (Fig. 14.2 completion arrow) | Fixed: the trainer ranks report "all shards fsynced" to the coordinator. |
| DT-12 (torn-tensor `[MEASURED]` claim) | Confirmed against the new GPU bundle (2026-11-06): GPU-resident tensors were not torn; Adam's CPU `step` scalars were staged by reference; the CPU-state run tore 43 data tensors, as the text says. |
| DT-13 (QD 32 latency 78 µs vs QD 1 80 µs) | Accepted. With 32 parallel flash channels the per-I/O latency can stay near the device latency; the value matches the lab's simulated fio run, which the manuscript cites. |
| DT-14, DT-15, OS-06, OS-14, F6 (concise), F7, F8, F12 | Accepted: first-order models or scope choices, labelled `[MODELED]` or covered in the full edition; recorded in the logs. |
| F9 (Capstone H cites full-edition section numbers) | Fixed: the capstone now names the sections and gives both editions' numbers. |
| F15, OS-12 (missing Appendix E rows) | Fixed by the sources review (Table E.13). |
| OS-13 (ch17 "in order" vs Figure 17.1) | Fixed: the text points to the figure for the evaluation order. |
| FEC-10 (ch24 job register stale after 2026-11-29) | **Fixed 2026-11-06:** register refreshed (60 requisitions, 50 roles, 11 employers; `docs/verification/G7-ch24-2026-11.md`); both editions, lab, R4 solver and key updated. New stale-after date 2026-12-06. |
| FEC-11 (KDP description wording) | Fixed: ORION stated as fictional; extension hardware stated correctly; checklist count corrected to 72. |
