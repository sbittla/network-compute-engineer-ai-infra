# ADR-001: Serving configuration for W-INFER on HX8

- **Status:** <fill>
- **Date:** <fill>
- **Deciders:** <fill: Inference, Platform, SRE, Finance>

## Context

<fill: traffic forecast and mix, SLOs, HX8 memory and bandwidth, FP8 quality status.>

## Options

| Option | Summary | Max SLO-compliant node load (mixed / chat-only) | $/M total tokens at that load | Main risk |
|---|---|---|---|---|
| c1 BF16 TP8 chunked | <fill> | <fill> | <fill> | <fill> |
| c2 BF16 TP8 big batch, no chunking | <fill> | | | |
| c3 FP8 TP4 × 2 per node | <fill> | | | |
| c4 BF16 TP8, 8k max length | <fill> | | | |

## Decision

<fill>

## Consequences

<fill: including how the long-context tenant is served; follow-ups with owners.>
