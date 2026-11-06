# 8.20 — Correlation versus a discriminating test (model answer)

Relies on manuscript Section 8.13 (the GID-index scenario, Table 8.8, the discriminating tests).

## Correlation-only evidence

Any of these signals points at `orion-n05`, but none justifies a change on its own:

- **Timing:** "the fleet configuration push happened shortly before the failures began". Many things
  change in a push, and many failures start after one.
- **Exclusion pattern:** "jobs that include orion-n05 fail; jobs without it start". This localizes the
  fault to n05 (or its links or leaf ports) but says nothing about *what* is wrong.
- **The env-file difference:** "n05 has `NCCL_IB_GID_INDEX=2` and n04 has 3". A difference is not a
  cause. Hosts can differ in harmless ways, and GID-table ordering differs between host groups, so 2
  might be correct on some hosts.

Acting on correlation alone risks a wrong change (for example rebooting or reimaging n05, or reverting
the whole push) that may hide the fault without explaining it.

## The missing causal link

1. **A mechanism that predicts every observation:** on HX8 hosts GID index 2 is the **RoCEv1** entry
   (`gid_attrs/types/2` = `IB/RoCE v1`). v1 frames (EtherType 0x8915, no IP header) are not routable on
   ORION's /31 rails. The leaf drops them as non-IP, so n05's ACKs never leave the leaf and peers see
   `local_ack_timeout_err` and `IBV_WC_RETRY_EXC_ERR`.
2. **Counters consistent with that mechanism:** zero TC 3 RoCE packets from n05 at `orion-be-leaf-r3`,
   rising non-IP/unknown-EtherType drops, no `out_of_sequence` (nothing arrives, so no gaps), and zero
   FEC/CRC errors.
3. **A test that changes only the suspected variable:** `ib_write_bw -x 3` (RoCEv2) between n04 and n05
   passes at ≈ 386 Gb/s; the same command with `-x 2` fails. Same nodes, NIC, cable and time; only the
   GID index differs. That converts correlation into causation, and it justifies the safe change: derive
   the GID index per host, canary on n05, then roll out.
