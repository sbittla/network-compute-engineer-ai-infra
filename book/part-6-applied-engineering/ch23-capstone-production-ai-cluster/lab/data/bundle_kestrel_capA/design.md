# ORION-256 capstone design -- Team Kestrel (Capstone A)

## Problem statement

Halcyon AI wants one cluster for W-TRAIN pretraining and W-INFER serving. Our target is a step time
of 17.4 s [MODELED] (B-01) and training goodput of at least 0.90 (SLO-01).

## Assumptions

See assumptions.yaml. We treat MFU (A-04) and job MTBF (A-07) as the decision-critical inputs,
and we assume the storage tier sustains the dataloader read rate (A-12).

## Architecture

We deploy 34 HX8 nodes (two extra for headroom) giving 256 training GPUs plus spare capacity.
TP=8 stays inside the NVLink domain; PP=4 and DP cross nodes.
The backend is a rail-optimised RoCEv2 leaf-spine with 8 rail leaves and 4 spines (topology.yaml).
Each rail leaf carries 400 Gb/s per port and the fabric is non-blocking.
Racks rack-01..rack-06 hold 4 nodes and rack-07..rack-08 hold 5 nodes; each node draws up to 10.2 kW [VENDOR-SPEC, 2026-10].
Rack power fits comfortably inside the facility envelope (A-09).

## Failure domains

The rail leaf (FD-04) is the largest blast radius. Storage metadata (FD-06) is shared by all jobs.

## Benchmark evidence

Our two-node NCCL run reached 356 GB/s busbw (B-02) and the eight-node run reached 328 GB/s (B-04).
Checkpoints should cost under 6 % of wall-clock time once asynchronous saves land.

## Next-step backlog

1. Measure A-04 on a 64-GPU slice.
2. Re-run B-04 on L3 hardware.
3. Add a spare rail leaf.
