# ORION-256 capstone design (reference bundle)

## Problem statement

Halcyon AI needs a cluster that trains W-TRAIN (70B dense, 4.19 M tokens per step) and serves
W-INFER from the same hardware estate. Success means a step time near 17.4 s [MODELED] (B-01) and a
training goodput SLO of 0.90 (SLO-01).

## Assumptions

All load-bearing numbers live in assumptions.yaml. The decision-critical ones are MFU (A-04),
job MTBF (A-07) and blocking checkpoint time (A-08).

## Architecture

32 HX8 nodes give 256 GPUs; TP=8 stays inside each NVLink domain, PP=4 and DP=8 cross nodes.
The backend is a rail-optimized RoCEv2 leaf-spine: 8 rail leaves of radix 64 with 32 downlinks and
32 uplinks each, and 4 spines, for 1:1 subscription (see topology.yaml).
Each GPU node draws up to 10.2 kW [VENDOR-SPEC, 2026-10] so a 4-node rack needs 40.8 kW [MODELED]
against the 45 kW planned budget (A-09: 50 kW rack limit less the 10 % transient margin).

## Failure domains

The rail leaf (FD-04) is the largest single-component blast radius: it touches every node.
Rack power (FD-06) is mitigated by spreading DP replicas across racks.

## Benchmark evidence

B-02 is the only fabric benchmark row; everything else is modeled. ORION is fictional and no run
produced B-02, so it is labelled ILLUSTRATIVE; a real 2-node run would make it MEASURED with its manifest.
Checkpoint plus rework waste at the Young interval is about 2.6 % [MODELED] (B-05), excluding restart.

## Failure exercise

A tabletop of a rail-leaf failure during a 256-GPU run: expected detection within 2 min
[ILLUSTRATIVE] via NCCL watchdog and switch link-down alerts. The job must restart from the last
checkpoint; the plan assumes it waits for the pre-staged spare leaf rather than relying on
untested 7-rail operation.

## Next-step backlog

1. Measure A-04 on a 64-GPU slice (highest decision value).
2. Validate A-08 at 32-node scale.
3. Pre-stage a spare rail leaf to cut FD-04 recovery time.
