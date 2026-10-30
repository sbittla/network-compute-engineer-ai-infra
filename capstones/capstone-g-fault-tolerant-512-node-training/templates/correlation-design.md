# Telemetry Correlation Logic

> Template for Capstone G artifact 2.

## 1. Sources

| Source | Identifier it carries | Clock | Maps to component via |
|---|---|---|---|
| Kernel (Xid, AER, mlx5 link) | PCI address | host | `<fill: BDF map; note Xid omits the function>` |
| DCGM | GPU UUID | host | `<fill>` |
| NIC counters | HCA name | host | `<fill>` |
| Switch counters | leaf, port | switch | `<fill: LLDP port map>` |
| Job / watchdog logs | rank | host | `<fill>` |
| Scheduler | node | controller | `<fill>` |

## 2. Time normalisation
`<fill: true = host_ts − offset; source of offsets (chrony tracking); what you do when an offset is unknown or > 1 s>`

## 3. Join keys and failure modes
`<fill: what breaks each join (renamed interfaces, re-enumerated BDFs after reset, stale LLDP) and how you detect it>`

## 4. Output schema
`<fill: columns of the normalised table and their units>`
