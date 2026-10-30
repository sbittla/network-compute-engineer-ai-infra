# Asynchronous Checkpoint and Restore Plan

> Template for Capstone G artifact 5.

## 1. Mechanism
`<fill: sharded async save (e.g. PyTorch DCP): snapshot to host memory, background upload, metadata commit as the consistency point; staging buffers; rate limiting>`

## 2. Interval derivation `[MODELED]`
`<fill: Young/Daly with your δ and M; arithmetic; chosen interval>`

## 3. Durability lag
`<fill: upload time and the fraction of time the newest started checkpoint is not restorable>`

## 4. Restorable-checkpoint criteria

| Criterion | How checked | This incident |
|---|---|---|
| Metadata committed | `<fill>` | `<fill>` |
| All shards present | | |
| Checksums verified | | |
| `<fill>` | | |

## 5. Restore validation
`<fill: first step = restored + 1; loss continuity tolerance and why; NaN checks; how long to watch>`

## 6. Retention
`<fill: how many checkpoints are kept, and why at least two durable ones>`
