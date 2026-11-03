# 7.T — Half the flows to rail 6 fail after a template push (★★★, L1)

Type: Troubleshooting case · kind: `written` · 20 points

## Prompt

<!-- prompt:start -->
**7.T** ★★★ L1 **[Outline: troubleshoot a scenario involving an MTU mismatch, asymmetric routing, or
incorrect route advertisement using a structured evidence checklist]**

*Evidence pack `[ILLUSTRATIVE]`.* On Thursday at 14:05 a configuration-template update was pushed to
`orion-be-leaf-r1`. From 14:06, a cross-rail benchmark (NCCL with PXN disabled, 16 nodes) shows roughly half
of the connections toward rail-6 NICs failing; NCCL logs contain lines such as:

```text
NET/IB : Got completion from peer 10.100.6.19<41022> with error 12, opcode 0, len 0, vendor err 129 (Recv)
```

(NCCL 2.18–2.19 form; 2.20–2.21 print `with status=12 opcode=0 len=0 …`, and 2.22+ print
`NET/IB: … status=12 … hca mlx5_N` `[VENDOR-SPEC, 2026-10]`; error 12 is `IBV_WC_RETRY_EXC_ERR`: the
transport retry counter was exceeded). Further evidence:

1. `orion-n04$ ping -c 5 -I 10.100.2.9 10.100.6.19` → 100 % loss. `ping -M do -s 8972` → 100 % loss.
   `ping -c 5 -I 10.100.6.9 10.100.6.19` (same rail) → 0 % loss.
2. From `orion-n04`'s rail-3 address to `10.100.6.19`: 0 % loss. From rail 5: 100 % loss.
3. A TCP sweep of 64 source ports from rail 2 to an `iperf3` server on `10.100.6.19`: 31 of 64
   connections never complete the handshake; the failures are the same at 1400-byte and 8948-byte MSS.
4. `orion-be-spine-1# show bgp ipv4 unicast 10.100.6.0/24`:

   ```text
   Paths: (16 available, best #1)
     65102                              <- via 10.101.1.17 (orion-be-leaf-r1), router-id 10.255.0.12, best
     65107                              <- via 10.101.1.97 (orion-be-leaf-r6), router-id 10.255.0.17
     ...
   ```

   `orion-be-spine-2` and `orion-be-spine-4` show the orion-be-leaf-r6 path as best; `orion-be-spine-3` shows the orion-be-leaf-r1 path as best.
5. Interface error counters on every fabric port are zero; every fabric link's MTU matches the intent.
6. `traceroute -n -T -p 41022 -s 10.100.2.9 10.100.6.19` shows `10.100.2.8` (orion-be-leaf-r2) →
   `10.101.1.32` (orion-be-spine-1) → `10.101.1.17` (orion-be-leaf-r1) → `* * *` for the remaining hops.
7. A colleague notes that forward and reverse traceroutes between the two NICs take different spines
   and proposes asymmetric routing as the root cause.
8. `show running-config | include bestpath` on each spine: `orion-be-spine-1` and `orion-be-spine-3`
   print `bgp bestpath compare-routerid` (left over from an older spine template);
   `orion-be-spine-2` and `orion-be-spine-4` print nothing. No spine has `as-path multipath-relax`.

Tasks: (a) Build the evidence checklist (Table 7.10 format) for MTU mismatch, asymmetric routing, and
incorrect advertisement, filling in what each hypothesis predicts and what the pack shows. (b) Rank
the hypotheses and name the root cause. (c) Explain why roughly half of the flows fail and why it is
the rail-2, rail-5 (and not the rail-3) sources that failed in this sample. (d) Respond to the
colleague in item 7. (e) Propose a safe fix, the validation evidence you would collect, and two
preventive controls.
*Evidence required:* a completed checklist table, ranked hypotheses with the discriminating evidence
cited by item number, and a fix/validate/prevent plan with measurable acceptance criteria.
<!-- prompt:end -->

## What to submit

Build the checklist as a Markdown table in the Table 7.10 format, and cite evidence by item number. Put every deliverable in `outputs/`:

- `outputs/answer.md`
