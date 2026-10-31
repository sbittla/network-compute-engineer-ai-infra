# R2 — What 2 s sampling hides (model answer)

Relies on manuscript Section 9.2 ("Microbursts and what counters can see"), Section 9.8 ("The counter
set", "Reading counters correctly") and lab README §5 (2 s sampling). Any two phenomena with their
revealing feature:

1. **Microbursts** (queues that fill and drain in tens of microseconds, for example the first RTT of an
   incast, ≈ 2 µs to Xoff in W2). An instantaneous queue-depth sample every 2 s almost never lands
   inside one, and cumulative counters average it away over 2 s. **Revealed by:** per-queue and per-PG
   **watermarks** (peak since last read, cleared on read; the lab's `q_tc3_max_kb`), plus the
   ECN-mark *count* delta showing marking happened.
2. **Short pause trains or brief storms** (a NIC that pauses for 200 ms, or a few dozen ms of pause
   propagation). A 2 s window turns them into a small average pause rate that looks harmless (24,000
   frames over 0.2 s reads as ≈ 12,000 /s across the window, or as nothing if it straddles a counter
   reset). **Revealed by:** **pause-duration counters** (time paused, not frames), PFC watchdog event
   logs, or sub-second streaming telemetry.
3. **Onset order of an incast or congestion tree** (which port went hot first, root vs branch). With 2 s
   resolution, every port turns hot "at the same time". **Revealed by:** high-rate or event-driven
   telemetry such as in-band network telemetry (INT) or mirror-on-drop/queue-threshold events with
   hardware timestamps.

Limitation to state: 2 s sampling is fine for *sustained* episodes (the lab's 58–70 s windows) but
says nothing about sub-second dynamics. A clean 2 s dashboard does not prove the absence of microbursts.
