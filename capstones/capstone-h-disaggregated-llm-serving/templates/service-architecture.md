# Service Architecture

> Template for Capstone H artifact 1. Replace every `<fill: …>`.

## 1. Diagram
`<fill: Mermaid diagram with gateway, admission, router, prefill pool, KV path, decode pool; caption it>`

## 2. Request path
| Step | Component | What happens | Latency budget |
|---|---|---|---|
| 1 | Gateway | auth, rate limit, admission | `<fill>` |
| 2 | Prefill | `<fill>` | `<fill>` |
| 3 | KV transfer | `<fill>` | `<fill>` |
| 4 | Decode | `<fill>` | `<fill>` |

## 3. Placement and routing
`<fill: how the router picks a prefill instance and a decode instance (KV capacity, batch size, locality on rails)>`

## 4. Ownership
`<fill: Inference, Fabric, Platform, SRE responsibilities>`
