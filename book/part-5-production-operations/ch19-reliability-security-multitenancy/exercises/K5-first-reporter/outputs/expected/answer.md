# K5 — The first reporter: worked solution

**Relies on:** Section 19.4 "NCCL timeout or hang"; Section 19.5 "Localizing with the flight recorder";
lab data `events.jsonl` and `rank_progress.csv` `[SIMULATED]`.

## Mechanism

PyTorch's process-group watchdog runs per rank. Each rank measures the time since *its own* oldest
incomplete collective was enqueued, and aborts when that exceeds the process-group timeout (10 min by
default for NCCL in PyTorch 2.x, `[VENDOR-SPEC, 2026-10]`). When one connection stops, ranks block at
*different* points: some inside the stuck all-reduce, others in a later send/recv waiting on the stuck
stage. Their timers started at different moments, so they expire in an essentially arbitrary order about
10 minutes after the fault. The first line in the log reflects timer start order and log latency, not
proximity to the fault. Every rank eventually times out, so the timeout itself localizes nothing.

Lab example: rank 817 on orionxl-n103 logs first at 03:51:01 (`SeqNum=88214, SEND`), yet it is in stage
1 on rail 1, nowhere near the stuck group. The ranks that were actually stuck log `SeqNum=88213,
ALLREDUCE` at 03:51:05.

## The two artifacts that localize a hang

1. **Flight-recorder dump (per-rank last completed sequence number).** The ranks with the *lowest*
   completed sequence number are the communicator that never finished. In the lab, 64 ranks stop at 88212
   while all others reached 88213; through the rank map they are local rank 5 on orionxl-n193–n256:
   rail 5, pipeline stage 3.
2. **Transport errors at stall onset.** NCCL `NET/IB … status=12` (retry counter exceeded) lines appear
   about one retry budget (≈ 8.6 s) after the fault, roughly 10 minutes *before* the watchdog. Their
   local and peer endpoints, resolved through the rank map, name the link: in the lab, orionxl-n212
   `mlx5_5` is named three times.

## Common wrong answers

- "Rank 0 logs first because it is the coordinator": wrong mechanism, and rank 0 is not first here.
- Naming the watchdog log as an artifact: it is present on all ranks and timed ≈ 10 min late.
- Naming only the scheduler failure event, which carries no locality at all.
