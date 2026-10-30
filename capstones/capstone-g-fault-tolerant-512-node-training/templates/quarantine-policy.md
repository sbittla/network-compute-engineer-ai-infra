# Quarantine Policy

> Template for Capstone G artifact 4.

## 1. Domains

| Fault class | Repair domain (quarantine) | Scheduling consequence (drain) | Why not smaller / larger |
|---|---|---|---|
| GPU uncontained ECC (Xid 95) | GPU | `<fill: drain immediately>` | `<fill>` |
| GPU contained ECC (Xid 94) | GPU | `<fill: drain when convenient, reset>` | |
| HCA / link flapping | `<fill>` | `<fill>` | |
| Switch port errors | `<fill>` | `<fill>` | |
| `<fill>` | | | |

## 2. Actions for this incident
`<fill: output of quarantine_plan() with a sentence per action>`

## 3. Evidence preservation
`<fill: what is captured before reset/repair (nvidia-smi -q, DCGM diag output, ethtool -S, switch counters, logs) and where it is stored>`

## 4. Return to service
`<fill: repair → reset → re-acceptance (Capstone E) → undrain; retry policy: what happens if the same device faults again within N days>`

## 5. Who may quarantine / release
`<fill: automation vs human; approvals; audit>`
