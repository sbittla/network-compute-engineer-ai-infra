# Audit Trail Specification

> Template for Capstone E artifact 6.

## 1. Record schema

| Field | Type | Required | Meaning |
|---|---|---|---|
| seq | int | yes | Monotonic, gap-free sequence number |
| utc | RFC 3339 string | yes | `<fill: whose clock? how is skew bounded?>` |
| actor | string | yes | `<fill: service identity or human; how authenticated>` |
| node | string | yes | |
| event | string | yes | |
| from_state / to_state | string | yes | |
| ticket | string | `<fill>` | Change or incident reference |
| evidence_sha256 | hex | `<fill>` | Hash of the acceptance evidence bundle |
| prev_hash | hex | yes | Hash of the previous record (genesis: 64 zeros) |
| hash | hex | yes | SHA-256 of the canonical JSON of the record without `hash` |
| `<fill>` | | | |

Canonicalisation rule: `<fill: e.g. JSON with sorted keys, no whitespace, UTF-8>` — state why it
matters.

## 2. Threat model

| Threat | Detected by hash chain alone? | Additional control |
|---|---|---|
| Edit of a past record | `<fill>` | `<fill>` |
| Deletion of a record | `<fill>` | `<fill>` |
| Truncation of the tail | `<fill>` | `<fill: external anchor of head hash>` |
| Rewrite of the whole chain by an admin | `<fill>` | `<fill>` |
| Forged record by a compromised automation identity | `<fill>` | `<fill: signing, least privilege>` |

## 3. Anchoring, retention and access

- Head-hash anchoring: `<fill: where, how often, owned by whom>`
- Retention: `<fill: duration and rationale>`
- Who can read / append / never modify: `<fill>`

## 4. Verification procedure

`<fill: numbered steps Security can follow, with the command and expected output for the supplied log>`

## 5. Result on the supplied export

`<fill: output of audit_verify() on data/audit_log.jsonl; what the broken record shows; what you would do next as an investigator>`
