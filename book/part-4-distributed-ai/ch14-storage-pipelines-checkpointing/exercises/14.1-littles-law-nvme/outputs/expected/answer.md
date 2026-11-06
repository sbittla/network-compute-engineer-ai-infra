# 14.1 — Little's law on NVMe: worked solution

**Formula (Little's law, Section 14.2):** L = λ × W, that is outstanding requests (queue depth) =
throughput (IOPS) × mean latency.

**(a) Queue depth 1.** With one request outstanding, the drive completes one request per latency
interval:

```text
IOPS = QD / latency = 1 / 95 µs = 1 / 95e-6 s = 10,526 IOPS
MB/s = 10,526 /s × 4,096 B = 43.1e6 B/s = 43.1 MB/s   (= 41.1 MiB/s)
```

A drive rated at about 1 M random-read IOPS delivers about 1 % of that at QD 1. The rating needs QD in
the hundreds across several queues.

**(b) Average queue depth from `iostat -x`:**

```text
QD = r/s × r_await = 330,000 /s × 0.097 × 10⁻³ s = 32.0
```

`iostat`'s `aqu-sz` column should read about 32 and is a cross-check.

**(c) Why `%util` = 100 % is not saturation.** `%util` is the fraction of wall time with *at least one*
request outstanding. That definition comes from single-queue rotating disks. An NVMe drive services
many requests in parallel across its flash channels and submission queues, so a QD-1 workload reads
100 % busy while using a few percent of the drive's capability. Saturation shows instead as **latency
rising with no further throughput gain as QD increases**, the knee of the latency-versus-QD curve
measured with fio (Section 14.6).

All results are `[MODELED]` from the stated inputs. The `iostat` values in (b) are given in the prompt
and are treated as `[ILLUSTRATIVE]` measurements.

**Common wrong answers.** Using 95 µs as 95 ms (off by 1,000). MB versus MiB without a label. Concluding
"the drive is saturated" from `%util`.
