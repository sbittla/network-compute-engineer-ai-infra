# K1 — Roles by what they are paged for: model answer

Source: Table 24.1 (Section 24.2), "Owns" and "Typically paged for" columns `[ILLUSTRATIVE]`. Any
well-justified variant earns full marks; the evidence column must name a real command, counter class or log.

| Role | Typical page / owned investigation | First evidence collected |
|---|---|---|
| AI Network Engineer | All-reduce bandwidth drop on one rail; PFC storm; link flap | Switch port counters (FEC corrected/uncorrectable, CRC, PFC pauses per priority, ECN marks); `ethtool -S <netdev>` on the hosts |
| GPU Compute / HPC Engineer | NCCL hang or an Xid error; a slow rank | Kernel log for Xid (`dmesg`, `journalctl -k`); `nvidia-smi -q`; NCCL logs with `NCCL_DEBUG=INFO` |
| AI Cluster / Platform Engineer | Jobs pending while GPUs are free; failed node return | `squeue` reason codes and `scontrol show job <id>`, or `kubectl describe pod` events; node health/drain state |
| AI Performance Engineer | Rarely paged: owns the regression investigation and launch readiness | Baseline vs current step-time distribution (mean, median, p99) with environment manifests |
| AI Infrastructure SRE / Operations | Paged first for any SLO burn alert, then escalates | The SLO's dashboard and burn rate, the change log for the window, the blast radius (which jobs/tenants) |
| Network Hardware / Vendor Engineer | Customer escalation on buffer drops, optics or firmware defects | The customer's counters plus switch OS/firmware and transceiver versions; a lab reproduction |

**Why this framing.** The paging column predicts interview content better than titles (Section 24.2): an
interviewer for an AI-network role will hand you port counters, one for GPU/HPC an Xid or NCCL log.

**Common mistakes.** Giving the performance engineer an on-call page without noting that it normally *owns*
investigations instead; "check the logs" with no named source; invented command flags (for example
non-existent `nvidia-smi` options). Deduct the specificity points for either.
